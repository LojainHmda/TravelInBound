def test_inbound_hotel_has_supplier_id_column(app):
    from app.models.inbound import InboundHotel
    col_names = [c.key for c in InboundHotel.__table__.columns]
    assert 'supplier_id' in col_names


def test_inbound_meal_has_supplier_id_column(app):
    from app.models.inbound import InboundMeal
    col_names = [c.key for c in InboundMeal.__table__.columns]
    assert 'supplier_id' in col_names


def test_inbound_transport_has_supplier_id_column(app):
    from app.models.inbound import InboundTransport
    col_names = [c.key for c in InboundTransport.__table__.columns]
    assert 'supplier_id' in col_names


def test_inbound_guide_has_supplier_id_column(app):
    from app.models.inbound import InboundGuide
    col_names = [c.key for c in InboundGuide.__table__.columns]
    assert 'supplier_id' in col_names


def test_hotel_supplier_fk_references_supplier_table(app):
    from app.models.inbound import InboundHotel
    fk = next(
        (fk for fk in InboundHotel.__table__.foreign_keys
         if 'supplier' in str(fk.column).lower()),
        None
    )
    assert fk is not None, "InboundHotel.supplier_id has no FK to supplier table"


def test_hotel_supplier_id_is_nullable(app):
    from app.models.inbound import InboundHotel
    col = InboundHotel.__table__.columns['supplier_id']
    assert col.nullable is True, "supplier_id must be nullable (existing rows have no supplier)"
