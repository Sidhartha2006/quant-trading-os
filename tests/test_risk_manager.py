
from bot.risk_manager import RiskManager


def test_allowed_risk():
    risk_manager = RiskManager(
        risk_percent=0.5,
        max_lots=0.5,
        max_open_positions=1
    )

    allowed_risk = risk_manager.calculate_allowed_risk(10000)

    assert allowed_risk == 50.0


def test_trade_risk():
    risk_manager = RiskManager()

    dollar_risk = risk_manager.calculate_trade_risk(
        price_risk=2.0,
        quantity=0.5
    )

    assert dollar_risk == 1.0


def test_position_size_allowed():
    risk_manager = RiskManager(
        max_lots=0.5
    )

    assert risk_manager.validate_position_size(0.5) is True


def test_position_size_rejected():
    risk_manager = RiskManager(
        max_lots=0.5
    )

    assert risk_manager.validate_position_size(0.6) is False


def test_open_position_allowed():
    risk_manager = RiskManager(
        max_open_positions=1
    )

    assert risk_manager.validate_open_positions(0) is True


def test_open_position_rejected():
    risk_manager = RiskManager(
        max_open_positions=1
    )

    assert risk_manager.validate_open_positions(1) is False


def test_trade_risk_allowed():
    risk_manager = RiskManager(
        risk_percent=0.5,
        max_lots=0.5,
        max_open_positions=1
    )

    trade = {
        "risk": 2.0
    }

    assert risk_manager.validate_trade(
        trade=trade,
        equity=10000,
        quantity=0.5
    ) is True


def test_trade_risk_rejected():
    risk_manager = RiskManager(
        risk_percent=0.5,
        max_lots=0.5,
        max_open_positions=1
    )

    trade = {
        "risk": 200.0
    }

    assert risk_manager.validate_trade(
        trade=trade,
        equity=10000,
        quantity=0.5
    ) is False

