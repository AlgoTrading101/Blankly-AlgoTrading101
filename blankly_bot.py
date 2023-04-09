import blankly

# The goal of this pairs trade strategy is
# to trade between two assets which DBX and BOX.
# We will calculate how much each stock moved in the past 5 days.
# If the difference between the two is greater than 5% we will
# long the stock that is underperforming
# and short the stock that is overperforming.


def init(symbol, state: blankly.FuturesStrategyState):
    state.variables["dbx_history"] = state.interface.history(
        "BOX", to=5, return_as="deque"
    )["close"]
    state.variables["box_history"] = state.interface.history(
        "DBX", to=5, return_as="deque"
    )["close"]

    state.variables["dbx_change"] = 0
    state.variables["box_change"] = 0

    state.variables["in_position"] = False
    state.variables["dbx_long"] = False
    state.variables["box_long"] = False

    state.variables["dbx_size"] = 0
    state.variables["box_size"] = 0


def price_event(price, symbol, state: blankly.FuturesStrategyState):
    # Add the new price to the history
    state.variables["dbx_history"].append(price["DBX"])
    state.variables["box_history"].append(price["BOX"])

    # Check if we have enough data to calculate the percentage change
    if (
        len(state.variables["dbx_history"]) == 5
        and len(state.variables["box_history"]) == 5
    ):
        # Calculate the percentage change
        state.variables["dbx_change"] = (
            state.variables["dbx_history"][-1] - state.variables["dbx_history"][0]
        ) / state.variables["dbx_history"][0]
        state.variables["box_change"] = (
            state.variables["box_history"][-1] - state.variables["box_history"][0]
        ) / state.variables["box_history"][0]

        # calculate the difference between the two stocks
        diff = state.variables["dbx_change"] - state.variables["box_change"]

        # If the difference is greater than 5% we will enter a position
        # We long the stock that is underperforming and short the stock that is overperforming
        if diff > 0.05 and not state.variables["in_position"]:
            # Calculate the size of the position
            # We allocate 40% of our portfolio to each position
            cash = state.interface.cash
            state.variables["dbx_size"] = blankly.trunc(
                (cash * 0.5 / state.interface.get_price("DBX")), 2
            )
            state.variables["box_size"] = blankly.trunc(
                (cash * 0.5 / state.interface.get_price("BOX")), 2
            )

            # Long BOX and short DBX
            try:
                state.interface.market_order(
                    "DBX", side="sell", size=state.variables["dbx_size"]
                )
                state.interface.market_order(
                    "BOX", side="buy", size=state.variables["box_size"]
                )
            except Exception as e:
                print(e)
                return

            state.variables["in_position"] = True
            state.variables["dbx_long"] = False
            state.variables["box_long"] = True

        # If the difference is less than -5% we will enter a position
        # We long the stock that is underperforming and short the stock that is overperforming
        elif diff < -0.05 and not state.variables["in_position"]:
            # We allocate 50% of our portfolio to each position
            cash = state.interface.cash
            state.variables["dbx_size"] = blankly.trunc(
                (cash * 0.5 / state.interface.get_price("DBX")), 2
            )
            state.variables["box_size"] = blankly.trunc(
                (cash * 0.5 / state.interface.get_price("BOX")), 2
            )

            # Short BOX and long DBX
            try:
                state.interface.market_order(
                    "BOX", side="sell", size=state.variables["box_size"]
                )
                state.interface.market_order(
                    "DBX", side="buy", size=state.variables["dbx_size"]
                )
            except Exception as e:
                print(e)
                return

            state.variables["in_position"] = True
            state.variables["dbx_long"] = True
            state.variables["box_long"] = False

        # If the position has reversed we reverse our position
        elif diff > 0.05 and state.variables["dbx_long"]:
            # Short DBX and long BOX
            try:
                state.interface.market_order(
                    "DBX", side="sell", size=state.variables["dbx_size"]
                )
                state.interface.market_order(
                    "BOX", side="buy", size=state.variables["box_size"]
                )
            except Exception as e:
                print(e)
                return

            state.variables["in_position"] = False
            state.variables["dbx_long"] = False
            state.variables["box_long"] = False

        elif diff < -0.05 and state.variables["box_long"]:
            # Long DBX and short BOX
            try:
                state.interface.market_order(
                    "BOX", side="sell", size=state.variables["box_size"]
                )
                state.interface.market_order(
                    "DBX", side="buy", size=state.variables["dbx_size"]
                )
            except Exception as e:
                print(e)
                return

            state.variables["in_position"] = False
            state.variables["dbx_long"] = False
            state.variables["box_long"] = False


if __name__ == "__main__":
    exchange = blankly.Alpaca()
    strategy = blankly.FuturesStrategy(exchange)

    strategy.add_arbitrage_event(
        price_event, symbols=["BOX", "DBX"], resolution="1d", init=init
    )
    backtest_result = strategy.backtest(initial_values={"USD": 10000}, to="3y")
    print(backtest_result)
