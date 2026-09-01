class RiskManager:

    def __init__(
        self,
        risk_percent=0.5,
        max_lots=0.5,
        max_open_positions=1
    ):

        self.risk_percent = float(
            risk_percent
        )

        self.max_lots = float(
            max_lots
        )

        self.max_open_positions = int(
            max_open_positions
        )


    # ========================================================
    # GET RISK PERCENT
    # ========================================================

    def get_risk_percent(self):

        return self.risk_percent


    # ========================================================
    # GET MAXIMUM LOTS
    # ========================================================

    def get_max_lots(self):

        return self.max_lots


    # ========================================================
    # GET MAX OPEN POSITIONS
    # ========================================================

    def get_max_open_positions(self):

        return self.max_open_positions


    # ========================================================
    # CALCULATE ALLOWED DOLLAR RISK
    # ========================================================

    def calculate_allowed_risk(
        self,
        equity
    ):

        equity = float(equity)

        allowed_risk = (
            equity
            * self.risk_percent
            / 100
        )

        return allowed_risk


    # ========================================================
    # CALCULATE TRADE DOLLAR RISK
    # ========================================================

    def calculate_trade_risk(
        self,
        price_risk,
        quantity
    ):

        price_risk = float(
            price_risk
        )

        quantity = float(
            quantity
        )

        dollar_risk = (
            price_risk
            * quantity
        )

        return dollar_risk


    # ========================================================
    # VALIDATE POSITION SIZE
    # ========================================================

    def validate_position_size(
        self,
        quantity
    ):

        quantity = float(
            quantity
        )

        # ----------------------------------------------------
        # VALID SIZE
        # ----------------------------------------------------

        if quantity <= self.max_lots:

            print()
            print("=" * 60)
            print("POSITION SIZE VALIDATED")
            print("=" * 60)

            print(
                f"Position Size    : "
                f"{quantity:.2f} lots"
            )

            print(
                f"Maximum Position: "
                f"{self.max_lots:.2f} lots"
            )

            print("=" * 60)

            return True


        # ----------------------------------------------------
        # INVALID SIZE
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("TRADE REJECTED — POSITION TOO LARGE")
        print("=" * 60)

        print(
            f"Position Size    : "
            f"{quantity:.2f} lots"
        )

        print(
            f"Maximum Position: "
            f"{self.max_lots:.2f} lots"
        )

        print("=" * 60)

        return False


    # ========================================================
    # VALIDATE OPEN POSITIONS
    # ========================================================

    def validate_open_positions(
        self,
        open_positions
    ):

        open_positions = int(
            open_positions
        )

        # ----------------------------------------------------
        # POSITION LIMIT NOT REACHED
        # ----------------------------------------------------

        if (
            open_positions
            < self.max_open_positions
        ):

            print()
            print("=" * 60)
            print("OPEN POSITION LIMIT VALIDATED")
            print("=" * 60)

            print(
                f"Open Positions   : "
                f"{open_positions}"
            )

            print(
                f"Maximum Allowed  : "
                f"{self.max_open_positions}"
            )

            print("=" * 60)

            return True


        # ----------------------------------------------------
        # POSITION LIMIT REACHED
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("TRADE REJECTED — MAX OPEN POSITIONS")
        print("=" * 60)

        print(
            f"Open Positions   : "
            f"{open_positions}"
        )

        print(
            f"Maximum Allowed  : "
            f"{self.max_open_positions}"
        )

        print("=" * 60)

        return False


    # ========================================================
    # VALIDATE COMPLETE TRADE
    # ========================================================

    def validate_trade(
        self,
        trade,
        equity,
        quantity=None
    ):

        equity = float(
            equity
        )

        # ----------------------------------------------------
        # POSITION SIZE
        # ----------------------------------------------------

        if quantity is None:

            quantity = float(
                trade.get(
                    "quantity",
                    self.max_lots
                )
            )

        else:

            quantity = float(
                quantity
            )


        # ----------------------------------------------------
        # PRICE RISK
        # ----------------------------------------------------

        price_risk = float(
            trade["risk"]
        )


        # ----------------------------------------------------
        # DOLLAR RISK
        # ----------------------------------------------------

        dollar_risk = (
            self.calculate_trade_risk(
                price_risk,
                quantity
            )
        )


        # ----------------------------------------------------
        # ALLOWED RISK
        # ----------------------------------------------------

        allowed_risk = (
            self.calculate_allowed_risk(
                equity
            )
        )


        # ====================================================
        # VALIDATE RISK
        # ====================================================

        if dollar_risk <= allowed_risk:

            print()
            print("=" * 60)
            print("TRADE RISK VALIDATED")
            print("=" * 60)

            print(
                f"Current Equity   : "
                f"${equity:.2f}"
            )

            print(
                f"Price Risk       : "
                f"{price_risk:.2f}"
            )

            print(
                f"Position Size    : "
                f"{quantity:.2f} lots"
            )

            print(
                f"Dollar Risk      : "
                f"${dollar_risk:.2f}"
            )

            print(
                f"Allowed Risk     : "
                f"${allowed_risk:.2f}"
            )

            print(
                f"Risk Limit       : "
                f"{self.risk_percent:.2f}%"
            )

            print("=" * 60)

            return True


        # ====================================================
        # REJECT
        # ====================================================

        print()
        print("=" * 60)
        print("TRADE REJECTED — RISK TOO HIGH")
        print("=" * 60)

        print(
            f"Current Equity   : "
            f"${equity:.2f}"
        )

        print(
            f"Price Risk       : "
            f"{price_risk:.2f}"
        )

        print(
            f"Position Size    : "
            f"{quantity:.2f} lots"
        )

        print(
            f"Dollar Risk      : "
            f"${dollar_risk:.2f}"
        )

        print(
            f"Allowed Risk     : "
            f"${allowed_risk:.2f}"
        )

        print(
            f"Risk Limit       : "
            f"{self.risk_percent:.2f}%"
        )

        print("=" * 60)

        return False