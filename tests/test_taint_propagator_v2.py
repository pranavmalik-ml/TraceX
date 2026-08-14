import unittest
from datetime import datetime
from decimal import Decimal

from taint_propagator_v2 import (
    TaintPropagatorV2,
    Transaction,
)


# ============================================================
# TEST HELPERS
# ============================================================

def txn(
    txn_id,
    sender,
    receiver,
    amount,
    minute=0
):
    return Transaction(
        txn_id=txn_id,
        sender=sender,
        receiver=receiver,
        amount=Decimal(str(amount)),
        timestamp=datetime(
            2026,
            8,
            14,
            10,
            minute,
            0
        )
    )


# ============================================================
# TEST SUITE
# ============================================================

class TestTaintPropagatorV2(unittest.TestCase):

    # --------------------------------------------------------
    # 1. BASIC ORIGIN
    # --------------------------------------------------------

    def test_initialize_origin(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            account_id="A",
            amount=Decimal("100000"),
            source_id="FRAUD_001"
        )

        account = propagator.get_account("A")

        self.assertEqual(
            account.total_balance,
            Decimal("100000")
        )

        self.assertEqual(
            account.tainted_balance,
            Decimal("100000")
        )

        self.assertEqual(
            account.clean_balance,
            Decimal("0")
        )

        self.assertEqual(
            account.taint_sources["FRAUD_001"],
            Decimal("100000")
        )

    # --------------------------------------------------------
    # 2. BASIC PROPAGATION
    # --------------------------------------------------------

    def test_basic_propagation(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "TXN001",
                "A",
                "B",
                40000
            )
        ]

        results = propagator.propagate(
            transactions
        )

        self.assertEqual(
            len(results),
            1
        )

        result = results[0]

        self.assertEqual(
            result["tainted_amount"],
            Decimal("40000")
        )

        self.assertEqual(
            result["clean_amount"],
            Decimal("0")
        )

        b = propagator.get_account("B")

        self.assertEqual(
            b.total_balance,
            Decimal("40000")
        )

        self.assertEqual(
            b.tainted_balance,
            Decimal("40000")
        )

        self.assertEqual(
            b.taint_sources["FRAUD_001"],
            Decimal("40000")
        )

    # --------------------------------------------------------
    # 3. CLEAN + TAINTED MIXING
    # --------------------------------------------------------

    def test_clean_tainted_mixing(self):

        propagator = TaintPropagatorV2()

        # A has ₹40k tainted
        propagator.initialize_origin(
            "A",
            Decimal("40000"),
            "FRAUD_001"
        )

        # C has ₹40k clean
        propagator.get_account(
            "C"
        ).total_balance = Decimal("40000")

        transactions = [

            txn(
                "TXN001",
                "A",
                "B",
                40000,
                0
            ),

            txn(
                "TXN002",
                "C",
                "B",
                40000,
                1
            ),

            txn(
                "TXN003",
                "B",
                "D",
                50000,
                2
            )
        ]

        results = propagator.propagate(
            transactions
        )

        result = results[2]

        # B had 50% taint.
        # ₹50k transfer → ₹25k tainted.
        self.assertEqual(
            result["tainted_amount"],
            Decimal("25000")
        )

        self.assertEqual(
            result["clean_amount"],
            Decimal("25000")
        )

        d = propagator.get_account("D")

        self.assertEqual(
            d.total_balance,
            Decimal("50000")
        )

        self.assertEqual(
            d.tainted_balance,
            Decimal("25000")
        )

        self.assertEqual(
            d.clean_balance,
            Decimal("25000")
        )

        self.assertEqual(
            d.taint_sources["FRAUD_001"],
            Decimal("25000")
        )

    # --------------------------------------------------------
    # 4. MULTIPLE FRAUD SOURCES
    # --------------------------------------------------------

    def test_multiple_fraud_sources(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("40000"),
            "FRAUD_001"
        )

        propagator.initialize_origin(
            "B",
            Decimal("20000"),
            "FRAUD_002"
        )

        transactions = [

            txn(
                "TXN001",
                "A",
                "C",
                40000,
                0
            ),

            txn(
                "TXN002",
                "B",
                "C",
                20000,
                1
            )
        ]

        propagator.propagate(
            transactions
        )

        c = propagator.get_account("C")

        self.assertEqual(
            c.total_balance,
            Decimal("60000")
        )

        self.assertEqual(
            c.tainted_balance,
            Decimal("60000")
        )

        self.assertEqual(
            c.taint_sources["FRAUD_001"],
            Decimal("40000")
        )

        self.assertEqual(
            c.taint_sources["FRAUD_002"],
            Decimal("20000")
        )

    # --------------------------------------------------------
    # 5. FAN-OUT
    # --------------------------------------------------------

    def test_fan_out(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [

            txn(
                "TXN001",
                "A",
                "B",
                30000,
                0
            ),

            txn(
                "TXN002",
                "A",
                "C",
                20000,
                1
            ),

            txn(
                "TXN003",
                "A",
                "D",
                10000,
                2
            )
        ]

        propagator.propagate(
            transactions
        )

        b = propagator.get_account("B")
        c = propagator.get_account("C")
        d = propagator.get_account("D")

        self.assertEqual(
            b.tainted_balance,
            Decimal("30000")
        )

        self.assertEqual(
            c.tainted_balance,
            Decimal("20000")
        )

        self.assertEqual(
            d.tainted_balance,
            Decimal("10000")
        )

        a = propagator.get_account("A")

        self.assertEqual(
            a.total_balance,
            Decimal("40000")
        )

        self.assertEqual(
            a.tainted_balance,
            Decimal("40000")
        )

    # --------------------------------------------------------
    # 6. FAN-IN
    # --------------------------------------------------------

    def test_fan_in(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("30000"),
            "FRAUD_001"
        )

        propagator.initialize_origin(
            "B",
            Decimal("20000"),
            "FRAUD_002"
        )

        transactions = [

            txn(
                "TXN001",
                "A",
                "C",
                30000,
                0
            ),

            txn(
                "TXN002",
                "B",
                "C",
                20000,
                1
            )
        ]

        propagator.propagate(
            transactions
        )

        c = propagator.get_account("C")

        self.assertEqual(
            c.total_balance,
            Decimal("50000")
        )

        self.assertEqual(
            c.tainted_balance,
            Decimal("50000")
        )

        self.assertEqual(
            c.taint_sources["FRAUD_001"],
            Decimal("30000")
        )

        self.assertEqual(
            c.taint_sources["FRAUD_002"],
            Decimal("20000")
        )

    # --------------------------------------------------------
    # 7. PARTIAL SPENDING
    # --------------------------------------------------------

    def test_partial_spending(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "TXN001",
                "A",
                "B",
                40000
            )
        ]

        propagator.propagate(
            transactions
        )

        a = propagator.get_account("A")

        self.assertEqual(
            a.total_balance,
            Decimal("60000")
        )

        self.assertEqual(
            a.tainted_balance,
            Decimal("60000")
        )

        self.assertEqual(
            a.taint_sources["FRAUD_001"],
            Decimal("60000")
        )

    # --------------------------------------------------------
    # 8. CYCLE
    # --------------------------------------------------------

    def test_cycle(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("70000"),
            "FRAUD_001"
        )

        transactions = [

            txn(
                "TXN001",
                "A",
                "B",
                40000,
                0
            ),

            txn(
                "TXN002",
                "B",
                "C",
                20000,
                1
            ),

            txn(
                "TXN003",
                "C",
                "A",
                10000,
                2
            )
        ]

        propagator.propagate(
            transactions
        )

        a = propagator.get_account("A")
        b = propagator.get_account("B")
        c = propagator.get_account("C")

        self.assertEqual(
            a.total_balance,
            Decimal("40000")
        )

        self.assertEqual(
            b.total_balance,
            Decimal("20000")
        )

        self.assertEqual(
            c.total_balance,
            Decimal("10000")
        )

        self.assertEqual(
            a.tainted_balance,
            Decimal("40000")
        )

        self.assertEqual(
            b.tainted_balance,
            Decimal("20000")
        )

        self.assertEqual(
            c.tainted_balance,
            Decimal("10000")
        )

    # --------------------------------------------------------
    # 9. INSUFFICIENT BALANCE
    # --------------------------------------------------------

    def test_insufficient_balance(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("10000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "TXN001",
                "A",
                "B",
                20000
            )
        ]

        with self.assertRaises(ValueError):

            propagator.propagate(
                transactions
            )

    # --------------------------------------------------------
    # 10. DUPLICATE TRANSACTION ID
    # --------------------------------------------------------

    def test_duplicate_transaction_id(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [

            txn(
                "TXN001",
                "A",
                "B",
                10000,
                0
            ),

            txn(
                "TXN001",
                "A",
                "C",
                10000,
                1
            )
        ]

        with self.assertRaises(ValueError):

            propagator.propagate(
                transactions
            )

    # --------------------------------------------------------
    # 11. SELF TRANSFER
    # --------------------------------------------------------

    def test_self_transfer(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "TXN001",
                "A",
                "A",
                10000
            )
        ]

        with self.assertRaises(ValueError):

            propagator.propagate(
                transactions
            )

    # --------------------------------------------------------
    # 12. NEGATIVE AMOUNT
    # --------------------------------------------------------

    def test_negative_amount(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "TXN001",
                "A",
                "B",
                -10000
            )
        ]

        with self.assertRaises(ValueError):

            propagator.propagate(
                transactions
            )

    # --------------------------------------------------------
    # 13. ZERO AMOUNT
    # --------------------------------------------------------

    def test_zero_amount(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "TXN001",
                "A",
                "B",
                0
            )
        ]

        with self.assertRaises(ValueError):

            propagator.propagate(
                transactions
            )

    # --------------------------------------------------------
    # 14. EMPTY TRANSACTION ID
    # --------------------------------------------------------

    def test_empty_transaction_id(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [
            txn(
                "",
                "A",
                "B",
                10000
            )
        ]

        with self.assertRaises(ValueError):

            propagator.propagate(
                transactions
            )

    # --------------------------------------------------------
    # 15. CHRONOLOGICAL ORDERING
    # --------------------------------------------------------

    def test_chronological_ordering(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        # Intentionally provide transactions
        # in the WRONG order.

        transactions = [

            txn(
                "TXN002",
                "B",
                "C",
                20000,
                2
            ),

            txn(
                "TXN001",
                "A",
                "B",
                20000,
                1
            )
        ]

        results = propagator.propagate(
            transactions
        )

        # Engine should process TXN001 first.
        self.assertEqual(
            results[0]["txn_id"],
            "TXN001"
        )

        self.assertEqual(
            results[1]["txn_id"],
            "TXN002"
        )

        c = propagator.get_account("C")

        self.assertEqual(
            c.tainted_balance,
            Decimal("20000")
        )

    # --------------------------------------------------------
    # 16. SOURCE CONSERVATION
    # --------------------------------------------------------

    def test_source_conservation(self):

        propagator = TaintPropagatorV2()

        propagator.initialize_origin(
            "A",
            Decimal("100000"),
            "FRAUD_001"
        )

        transactions = [

            txn(
                "TXN001",
                "A",
                "B",
                40000,
                0
            ),

            txn(
                "TXN002",
                "B",
                "C",
                20000,
                1
            )
        ]

        propagator.propagate(
            transactions
        )

        total_source_amount = Decimal("0")

        for account in propagator.accounts.values():

            total_source_amount += sum(
                account.taint_sources.values(),
                Decimal("0")
            )

        # Original fraud amount was ₹100,000.
        # No money disappeared from the tracked system.
        self.assertEqual(
            total_source_amount,
            Decimal("100000")
        )

    # --------------------------------------------------------
    # 17. MULTIPLE SOURCES + MIXING
    # --------------------------------------------------------

    def test_multiple_sources_with_clean_mixing(self):

        propagator = TaintPropagatorV2()

        # Fraud source 1
        propagator.initialize_origin(
            "A",
            Decimal("40000"),
            "FRAUD_001"
        )

        # Fraud source 2
        propagator.initialize_origin(
            "B",
            Decimal("20000"),
            "FRAUD_002"
        )

        # Clean money
        propagator.get_account(
            "C"
        ).total_balance = Decimal("40000")

        transactions = [

            txn(
                "TXN001",
                "A",
                "D",
                40000,
                0
            ),

            txn(
                "TXN002",
                "B",
                "D",
                20000,
                1
            ),

            txn(
                "TXN003",
                "C",
                "D",
                40000,
                2
            ),

            # D now:
            #
            # FRAUD_001 = 40k
            # FRAUD_002 = 20k
            # CLEAN     = 40k
            # TOTAL     = 100k
            #
            # Taint fraction = 60%
            #
            # D → E ₹50k
            #
            # FRAUD_001 = 20k
            # FRAUD_002 = 10k
            # Clean     = 20k

            txn(
                "TXN004",
                "D",
                "E",
                50000,
                3
            )
        ]

        results = propagator.propagate(
            transactions
        )

        result = results[3]

        self.assertEqual(
            result["tainted_amount"],
            Decimal("30000")
        )

        self.assertEqual(
            result["clean_amount"],
            Decimal("20000")
        )

        e = propagator.get_account("E")

        self.assertEqual(
            e.total_balance,
            Decimal("50000")
        )

        self.assertEqual(
            e.tainted_balance,
            Decimal("30000")
        )

        self.assertEqual(
            e.clean_balance,
            Decimal("20000")
        )

        self.assertEqual(
            e.taint_sources["FRAUD_001"],
            Decimal("20000")
        )

        self.assertEqual(
            e.taint_sources["FRAUD_002"],
            Decimal("10000")
        )


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)