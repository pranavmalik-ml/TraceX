from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


# ============================================================
# TRANSACTION
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

    @property
    def clean_balance(self) -> Decimal:
        return self.total_balance - self.tainted_balance

    @property
    def taint_fraction(self) -> Decimal:
        if self.total_balance <= 0:
            return Decimal("0")

        return self.tainted_balance / self.total_balance


# ============================================================
# TAINT PROPAGATOR
# ============================================================

class TaintPropagator:

    def __init__(self):
        self.accounts: Dict[str, AccountState] = {}
        self.transaction_results: List[dict] = []

    # ========================================================
    # GET / CREATE ACCOUNT
    # ========================================================

    def get_account(self, account_id: str) -> AccountState:
        """
        Return an existing account state or create a new one.
        """

        if account_id not in self.accounts:
            self.accounts[account_id] = AccountState()

        return self.accounts[account_id]

    # ========================================================
    # VALIDATE TRANSACTION
    # ========================================================

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
                f"Sender cannot be empty: {txn.txn_id}"
            )

        if not txn.receiver:
            raise ValueError(
                f"Receiver cannot be empty: {txn.txn_id}"
            )

        if txn.sender == txn.receiver:
            raise ValueError(
                f"Self-transfer detected: {txn.txn_id}"
            )

        if txn.amount <= 0:
            raise ValueError(
                f"Transaction amount must be positive: "
                f"{txn.txn_id}"
            )

        if not isinstance(txn.amount, Decimal):
            raise TypeError(
                f"Transaction amount must be Decimal: "
                f"{txn.txn_id}"
            )

        if not isinstance(txn.timestamp, datetime):
            raise TypeError(
                f"Timestamp must be datetime: "
                f"{txn.txn_id}"
            )

    # ========================================================
    # PREPARE TRANSACTIONS
    # ========================================================

    def prepare_transactions(
        self,
        transactions: List[Transaction]
    ) -> List[Transaction]:

        if not transactions:
            raise ValueError(
                "Transaction list cannot be empty"
            )

        for txn in transactions:
            self.validate_transaction(txn)

        # Chronological order.
        #
        # txn_id is used as a deterministic tie-breaker
        # when timestamps are identical.
        return sorted(
            transactions,
            key=lambda txn: (
                txn.timestamp,
                txn.txn_id
            )
        )

    # ========================================================
    # INITIALIZE FRAUD ORIGIN
    # ========================================================

    def initialize_origin(
        self,
        receiver: str,
        amount: Decimal
    ) -> None:

        if not receiver:
            raise ValueError(
                "Origin receiver cannot be empty"
            )

        if amount <= 0:
            raise ValueError(
                "Origin amount must be positive"
            )

        account = self.get_account(receiver)

        account.total_balance += amount
        account.tainted_balance += amount

        self.validate_state(
            receiver,
            account
        )

    # ========================================================
    # PROCESS INCOMING
    # ========================================================

    def process_incoming(
        self,
        sender: AccountState,
        receiver: AccountState,
        amount: Decimal
    ) -> Decimal:

        if amount <= 0:
            raise ValueError(
                "Incoming amount must be positive"
            )

        # If sender has no tracked balance,
        # no taint can be attributed.
        if sender.total_balance <= 0:
            tainted_amount = Decimal("0")

        else:
            tainted_amount = (
                amount * sender.taint_fraction
            )

        receiver.total_balance += amount
        receiver.tainted_balance += tainted_amount

        return tainted_amount

    # ========================================================
    # PROCESS OUTGOING
    # ========================================================

    def process_outgoing(
        self,
        sender: AccountState,
        amount: Decimal
    ) -> Decimal:

        if amount <= 0:
            raise ValueError(
                "Outgoing amount must be positive"
            )

        if amount > sender.total_balance:
            raise ValueError(
                "Insufficient tracked balance"
            )

        if sender.total_balance <= 0:
            return Decimal("0")

        tainted_amount = (
            amount * sender.taint_fraction
        )

        sender.total_balance -= amount
        sender.tainted_balance -= tainted_amount

        return tainted_amount

    # ========================================================
    # VALIDATE ACCOUNT STATE
    # ========================================================

    def validate_state(
        self,
        account_id: str,
        state: AccountState
    ) -> None:

        if state.total_balance < 0:
            raise RuntimeError(
                f"Negative balance for {account_id}"
            )

        if state.tainted_balance < 0:
            raise RuntimeError(
                f"Negative tainted balance for "
                f"{account_id}"
            )

        if state.tainted_balance > state.total_balance:
            raise RuntimeError(
                f"Tainted balance exceeds total balance "
                f"for {account_id}"
            )

    # ========================================================
    # PROCESS ONE TRANSACTION
    # ========================================================

    def process_transaction(
        self,
        txn: Transaction
    ) -> dict:

        sender = self.get_account(txn.sender)
        receiver = self.get_account(txn.receiver)

        # ----------------------------------------------------
        # Remove money from sender
        # ----------------------------------------------------

        tainted_amount = self.process_outgoing(
            sender,
            txn.amount
        )

        # ----------------------------------------------------
        # Add money to receiver
        # ----------------------------------------------------

        receiver.total_balance += txn.amount
        receiver.tainted_balance += tainted_amount

        # ----------------------------------------------------
        # Validate both states
        # ----------------------------------------------------

        self.validate_state(
            txn.sender,
            sender
        )

        self.validate_state(
            txn.receiver,
            receiver
        )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        result = {
            "txn_id": txn.txn_id,
            "sender": txn.sender,
            "receiver": txn.receiver,
            "amount": txn.amount,
            "tainted_amount": tainted_amount,
            "clean_amount": (
                txn.amount - tainted_amount
            ),
        }

        self.transaction_results.append(result)

        return result

    # ========================================================
    # PROPAGATE
    # ========================================================

    def propagate(
        self,
        transactions: List[Transaction],
        origin_txn_id: str,
        initial_balances: Optional[
            Dict[str, Decimal]
        ] = None
    ) -> Dict[str, AccountState]:

        # ----------------------------------------------------
        # 1. Basic validation
        # ----------------------------------------------------

        if not transactions:
            raise ValueError(
                "Transaction list cannot be empty"
            )

        if not origin_txn_id:
            raise ValueError(
                "Origin transaction ID cannot be empty"
            )

        # ----------------------------------------------------
        # 2. Validate + sort
        # ----------------------------------------------------

        prepared = self.prepare_transactions(
            transactions
        )

        # ----------------------------------------------------
        # 3. Detect duplicate transaction IDs
        # ----------------------------------------------------

        txn_ids = [
            txn.txn_id
            for txn in prepared
        ]

        if len(txn_ids) != len(set(txn_ids)):
            raise ValueError(
                "Duplicate transaction ID detected"
            )

        # ----------------------------------------------------
        # 4. Find origin transaction
        # ----------------------------------------------------

        origin = None

        for txn in prepared:

            if txn.txn_id == origin_txn_id:
                origin = txn
                break

        if origin is None:
            raise ValueError(
                f"Origin transaction not found: "
                f"{origin_txn_id}"
            )

        # ----------------------------------------------------
        # 5. Reset previous state
        # ----------------------------------------------------

        self.accounts.clear()
        self.transaction_results.clear()

        # ----------------------------------------------------
        # 6. Load initial clean balances
        # ----------------------------------------------------

        if initial_balances:

            for account_id, balance in (
                initial_balances.items()
            ):

                if not account_id:
                    raise ValueError(
                        "Initial balance account ID "
                        "cannot be empty"
                    )

                if not isinstance(
                    balance,
                    Decimal
                ):
                    raise TypeError(
                        f"Initial balance for "
                        f"{account_id} must be Decimal"
                    )

                if balance < 0:
                    raise ValueError(
                        f"Initial balance cannot be "
                        f"negative: {account_id}"
                    )

                account = self.get_account(
                    account_id
                )

                account.total_balance = balance
                account.tainted_balance = Decimal("0")

                self.validate_state(
                    account_id,
                    account
                )

        # ----------------------------------------------------
        # 7. Initialize fraud origin
        # ----------------------------------------------------

        self.initialize_origin(
            receiver=origin.receiver,
            amount=origin.amount
        )

        # ----------------------------------------------------
        # 8. Process transactions after origin
        # ----------------------------------------------------

        origin_found = False

        for txn in prepared:

            # ----------------------------------------------
            # Origin itself is already initialized.
            # Do NOT process it again.
            # ----------------------------------------------

            if txn.txn_id == origin_txn_id:

                origin_found = True
                continue

            # ----------------------------------------------
            # Ignore transactions before origin.
            # ----------------------------------------------

            if not origin_found:
                continue

            # ----------------------------------------------
            # Process transaction
            # ----------------------------------------------

            self.process_transaction(txn)

        # ----------------------------------------------------
        # 9. Validate all final account states
        # ----------------------------------------------------

        for account_id, state in self.accounts.items():

            self.validate_state(
                account_id,
                state
            )

        # ----------------------------------------------------
        # 10. Return final states
        # ----------------------------------------------------

        return self.accounts


# ============================================================
# TEST HELPERS
# ============================================================

def print_accounts(
    accounts: Dict[str, AccountState]
) -> None:

    print("\nFinal Account States")
    print("====================")

    for account_id, state in accounts.items():

        print(f"\nAccount: {account_id}")
        print(f"Total: {state.total_balance}")
        print(f"Tainted: {state.tainted_balance}")
        print(f"Clean: {state.clean_balance}")
        print(
            f"Taint Fraction: "
            f"{state.taint_fraction}"
        )


def print_transactions(
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


# ============================================================
# TEST
# ============================================================
