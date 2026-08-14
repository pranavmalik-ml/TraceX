from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List


# ============================================================
# TRANSACTION MODEL
# ============================================================

@dataclass(frozen=True)
class Transaction:
    txn_id: str
    sender: str
    receiver: str
    amount: Decimal
    timestamp: datetime


# ============================================================
# ACCOUNT STATE
# ============================================================

@dataclass
class AccountState:
    total_balance: Decimal = Decimal("0")
    tainted_balance: Decimal = Decimal("0")

    # V2:
    # Tracks exactly which fraud source contributed tainted money.
    #
    # Example:
    # {
    #     "FRAUD_001": Decimal("25000"),
    #     "FRAUD_002": Decimal("15000")
    # }
    taint_sources: Dict[str, Decimal] = field(default_factory=dict)

    @property
    def clean_balance(self) -> Decimal:
        return self.total_balance - self.tainted_balance

    @property
    def taint_fraction(self) -> Decimal:
        if self.total_balance <= 0:
            return Decimal("0")

        return self.tainted_balance / self.total_balance


# ============================================================
# TAINT PROPAGATOR V2
# ============================================================

class TaintPropagatorV2:

    def __init__(self):
        self.accounts: Dict[str, AccountState] = {}
        self.transaction_results: List[dict] = []

    # --------------------------------------------------------
    # GET OR CREATE ACCOUNT
    # --------------------------------------------------------

    def get_account(self, account_id: str) -> AccountState:

        if not account_id:
            raise ValueError(
                "Account ID cannot be empty"
            )

        if account_id not in self.accounts:
            self.accounts[account_id] = AccountState()

        return self.accounts[account_id]

    # --------------------------------------------------------
    # INITIALIZE FRAUD ORIGIN
    # --------------------------------------------------------

    def initialize_origin(
        self,
        account_id: str,
        amount: Decimal,
        source_id: str
    ) -> None:

        if not account_id:
            raise ValueError(
                "Account ID cannot be empty"
            )

        if not source_id:
            raise ValueError(
                "Source ID cannot be empty"
            )

        if amount <= 0:
            raise ValueError(
                "Origin amount must be positive"
            )

        account = self.get_account(account_id)

        # Add total money
        account.total_balance += amount

        # Since this is the fraud origin,
        # the entire amount is considered tainted.
        account.tainted_balance += amount

        # Track the source
        account.taint_sources[source_id] = (
            account.taint_sources.get(
                source_id,
                Decimal("0")
            )
            + amount
        )

        self.validate_state(
            account_id,
            account
        )

    # --------------------------------------------------------
    # PROCESS OUTGOING TRANSACTION
    # --------------------------------------------------------

    def process_outgoing(
        self,
        sender: AccountState,
        amount: Decimal
    ) -> Dict[str, Decimal]:

        if amount <= 0:
            raise ValueError(
                "Transaction amount must be positive"
            )

        # We cannot spend more money than the
        # propagator is currently tracking.
        if amount > sender.total_balance:
            raise ValueError(
                "Insufficient tracked balance"
            )

        if sender.total_balance <= 0:
            return {}

        transferred_sources: Dict[str, Decimal] = {}

        # ----------------------------------------------------
        # PROPORTIONAL TAINT PROPAGATION
        # ----------------------------------------------------
        #
        # Example:
        #
        # Total = 100000
        # FRAUD_001 = 40000
        # FRAUD_002 = 20000
        # Clean = 40000
        #
        # Transaction = 50000
        #
        # FRAUD_001:
        # 50000 * 40000 / 100000 = 20000
        #
        # FRAUD_002:
        # 50000 * 20000 / 100000 = 10000
        #
        # Total tainted transferred = 30000
        # Clean transferred = 20000
        # ----------------------------------------------------

        original_total = sender.total_balance

        for source_id, source_amount in list(
            sender.taint_sources.items()
        ):

            transferred_amount = (
                amount
                * source_amount
                / original_total
            )

            transferred_sources[source_id] = (
                transferred_sources.get(
                    source_id,
                    Decimal("0")
                )
                + transferred_amount
            )

        # Total tainted money leaving sender
        total_transferred_taint = sum(
            transferred_sources.values(),
            Decimal("0")
        )

        # Remove total money
        sender.total_balance -= amount

        # Remove tainted money
        sender.tainted_balance -= (
            total_transferred_taint
        )

        # Remove individual source amounts
        for (
            source_id,
            transferred_amount
        ) in transferred_sources.items():

            sender.taint_sources[source_id] -= (
                transferred_amount
            )

            # Avoid tiny Decimal leftovers
            if sender.taint_sources[source_id] <= 0:
                del sender.taint_sources[source_id]

        return transferred_sources

    # --------------------------------------------------------
    # PROCESS INCOMING TRANSACTION
    # --------------------------------------------------------

    def process_incoming(
        self,
        receiver: AccountState,
        amount: Decimal,
        taint_sources: Dict[str, Decimal]
    ) -> None:

        if amount <= 0:
            raise ValueError(
                "Incoming amount must be positive"
            )

        # Add total incoming money
        receiver.total_balance += amount

        # Calculate total tainted amount
        transferred_taint = sum(
            taint_sources.values(),
            Decimal("0")
        )

        # Add tainted amount
        receiver.tainted_balance += (
            transferred_taint
        )

        # Add each individual source
        for (
            source_id,
            source_amount
        ) in taint_sources.items():

            receiver.taint_sources[source_id] = (
                receiver.taint_sources.get(
                    source_id,
                    Decimal("0")
                )
                + source_amount
            )

    # --------------------------------------------------------
    # PROCESS COMPLETE TRANSACTION
    # --------------------------------------------------------

    def process_transaction(
        self,
        txn: Transaction
    ) -> dict:

        # Basic validation
        self.validate_transaction(txn)

        sender = self.get_account(
            txn.sender
        )

        receiver = self.get_account(
            txn.receiver
        )

        # Take money out of sender
        transferred_sources = (
            self.process_outgoing(
                sender,
                txn.amount
            )
        )

        # Put money into receiver
        self.process_incoming(
            receiver,
            txn.amount,
            transferred_sources
        )

        # Calculate total taint
        tainted_amount = sum(
            transferred_sources.values(),
            Decimal("0")
        )

        clean_amount = (
            txn.amount - tainted_amount
        )

        # Validate both accounts
        self.validate_state(
            txn.sender,
            sender
        )

        self.validate_state(
            txn.receiver,
            receiver
        )

        # Store transaction result
        result = {
            "txn_id": txn.txn_id,
            "sender": txn.sender,
            "receiver": txn.receiver,
            "amount": txn.amount,
            "tainted_amount": tainted_amount,
            "clean_amount": clean_amount,
            "taint_sources": dict(
                transferred_sources
            )
        }

        self.transaction_results.append(
            result
        )

        return result

    # --------------------------------------------------------
    # VALIDATE TRANSACTION
    # --------------------------------------------------------

    def validate_transaction(
        self,
        txn: Transaction
    ) -> None:

        if not txn.txn_id:
            raise ValueError(
                "Transaction ID cannot be empty"
            )

        if not txn.sender:
            raise ValueError(
                "Sender cannot be empty"
            )

        if not txn.receiver:
            raise ValueError(
                "Receiver cannot be empty"
            )

        if txn.sender == txn.receiver:
            raise ValueError(
                f"Self-transfer detected: "
                f"{txn.txn_id}"
            )

        if txn.amount <= 0:
            raise ValueError(
                f"Transaction amount must be "
                f"positive: {txn.txn_id}"
            )

        if not isinstance(
            txn.timestamp,
            datetime
        ):
            raise TypeError(
                f"Timestamp must be datetime: "
                f"{txn.txn_id}"
            )

    # --------------------------------------------------------
    # VALIDATE ACCOUNT STATE
    # --------------------------------------------------------

    def validate_state(
        self,
        account_id: str,
        state: AccountState
    ) -> None:

        if state.total_balance < 0:
            raise RuntimeError(
                f"Negative balance for "
                f"{account_id}"
            )

        if state.tainted_balance < 0:
            raise RuntimeError(
                f"Negative tainted balance for "
                f"{account_id}"
            )

        if state.tainted_balance > state.total_balance:
            raise RuntimeError(
                f"Tainted balance exceeds "
                f"total balance for {account_id}"
            )

        # Make sure individual source amounts
        # add up to the account's tainted balance.
        source_total = sum(
            state.taint_sources.values(),
            Decimal("0")
        )

        if source_total != state.tainted_balance:
            raise RuntimeError(
                f"Taint source total does not match "
                f"tainted balance for {account_id}. "
                f"Sources = {source_total}, "
                f"Tainted = {state.tainted_balance}"
            )

    # --------------------------------------------------------
    # PROCESS MULTIPLE TRANSACTIONS
    # --------------------------------------------------------

    def propagate(
        self,
        transactions: List[Transaction]
    ) -> List[dict]:

        # Clear previous results
        self.transaction_results = []

        # Check duplicate transaction IDs
        transaction_ids = set()

        for txn in transactions:

            if txn.txn_id in transaction_ids:
                raise ValueError(
                    f"Duplicate transaction ID "
                    f"detected: {txn.txn_id}"
                )

            transaction_ids.add(
                txn.txn_id
            )

        # Validate all transactions
        for txn in transactions:
            self.validate_transaction(txn)

        # Process chronologically
        sorted_transactions = sorted(
            transactions,
            key=lambda txn: (
                txn.timestamp,
                txn.txn_id
            )
        )

        # Process each transaction
        for txn in sorted_transactions:
            self.process_transaction(txn)

        return self.transaction_results


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_account_states(
    propagator: TaintPropagatorV2
) -> None:

    print("\nFinal Account States")
    print("====================")

    for (
        account_id,
        account
    ) in propagator.accounts.items():

        print(f"\nAccount: {account_id}")
        print(
            f"Total: {account.total_balance}"
        )
        print(
            f"Tainted: {account.tainted_balance}"
        )
        print(
            f"Clean: {account.clean_balance}"
        )
        print(
            f"Taint Fraction: "
            f"{account.taint_fraction}"
        )

        print("Taint Sources:")

        if account.taint_sources:

            for (
                source_id,
                amount
            ) in account.taint_sources.items():

                print(
                    f"  {source_id}: "
                    f"{amount}"
                )

        else:
            print("  None")


def print_transaction_results(
    results: List[dict]
) -> None:

    print("\nTransaction Results")
    print("===================")

    for result in results:

        print(
            f"{result['txn_id']}: "
            f"{result['sender']} → "
            f"{result['receiver']} | "
            f"Amount = {result['amount']} | "
            f"Tainted = "
            f"{result['tainted_amount']} | "
            f"Clean = "
            f"{result['clean_amount']}"
        )

        if result["taint_sources"]:

            print("  Sources:")

            for (
                source_id,
                amount
            ) in result["taint_sources"].items():

                print(
                    f"    {source_id}: "
                    f"{amount}"
                )


# ============================================================
# TEST
# ============================================================

