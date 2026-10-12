"""Room categories per hotel: storage rules and finance JSON-notes handling.

Pure logic tests: nothing here touches the database.
"""
import json

from app.models.supplier import (
    BASE_ROOM_CATEGORIES,
    Supplier,
    normalize_room_categories,
    parse_room_categories_field,
)
from app.routes.finance import _merge_supplier_notes_json, _parse_supplier_notes


def test_hotel_with_nothing_saved_gets_the_4_base_categories():
    assert Supplier(notes=None).get_room_categories() == BASE_ROOM_CATEGORIES
    assert Supplier(notes='Just a note').get_room_categories() == BASE_ROOM_CATEGORIES


def test_legacy_json_notes_are_read():
    notes = json.dumps({'room_categories': ['abc'], 'room_category': 'Standard Rooms'})
    assert Supplier(notes=notes).get_room_categories() == ['abc', 'Standard Rooms']


def test_legacy_text_notes_are_read():
    notes = 'Payment Method: Cash\nRoom Category: King Suite\nCategory: 5-Star'
    assert Supplier(notes=notes).get_room_categories() == ['King Suite']


def test_saved_list_wins_over_legacy_notes():
    hotel = Supplier(notes='Room Category: King Suite')
    hotel.set_room_categories(['Deluxe', 'Sea View'])
    assert hotel.get_room_categories() == ['Deluxe', 'Sea View']


def test_saved_empty_list_stays_empty():
    hotel = Supplier(notes='Room Category: King Suite')
    hotel.set_room_categories([])
    assert hotel.room_categories == '[]'
    assert hotel.get_room_categories() == []


def test_names_are_cleaned_without_renaming():
    assert normalize_room_categories([' Deluxe ', 'deluxe', '', None, 'Junior Suites']) == ['Deluxe', 'Junior Suites']
    assert normalize_room_categories(['x' * 150]) == ['x' * 100]


def test_arabic_names_are_stored_readably():
    hotel = Supplier()
    hotel.set_room_categories(['جناح ملكي'])
    assert 'جناح ملكي' in hotel.room_categories
    assert hotel.get_room_categories() == ['جناح ملكي']


def test_form_field_parsing_never_wipes_on_bad_input():
    assert parse_room_categories_field(None) is None
    assert parse_room_categories_field('') is None
    assert parse_room_categories_field('not json') is None
    assert parse_room_categories_field('{"a": 1}') is None
    assert parse_room_categories_field('[]') == []
    assert parse_room_categories_field('["Suite", " suite ", "King Suite"]') == ['Suite', 'King Suite']


def test_finance_edit_reads_json_notes():
    notes = json.dumps({'category': 'Camp', 'payment_method': 'Cash', 'original_notes': 'Gate code 12',
                        'contract_file': 'a.pdf', 'bed_types': ['King']})
    parsed = _parse_supplier_notes(notes)
    assert (parsed['category'], parsed['custom_category']) == ('Camp', '')
    assert parsed['payment_method_embedded'] == 'Cash'
    assert parsed['clean_notes'] == 'Gate code 12'
    assert parsed['contract_file'] == 'a.pdf'
    assert parsed['notes_json']['bed_types'] == ['King']


def test_finance_edit_json_custom_category_round_trip():
    parsed = _parse_supplier_notes(json.dumps({'category': 'Glamping'}))
    assert (parsed['category'], parsed['custom_category']) == ('Other', 'Glamping')
    merged = json.loads(_merge_supplier_notes_json(parsed['notes_json'], '', 'Other', 'Glamping', '', ''))
    assert merged == {'category': 'Glamping'}


def test_finance_edit_keeps_other_json_keys():
    notes_json = {'category': 'Camp', 'payment_method': 'Cash', 'bed_types': ['King'],
                  'room_categories': ['abc']}
    merged = json.loads(_merge_supplier_notes_json(notes_json, 'New note', '4-Star', '', '', ''))
    assert merged == {'category': '4-Star', 'original_notes': 'New note',
                      'bed_types': ['King'], 'room_categories': ['abc']}


def test_finance_edit_json_keeps_contract_when_no_new_upload():
    # edit_supplier_type: contract_saved_name starts as parsed_existing['contract_file'] and is
    # only replaced when a new file is uploaded, so the JSON merge must keep it.
    notes = json.dumps({'category': 'Camp', 'contract_file': '20260101_contract.pdf', 'bed_types': ['King']})
    parsed_existing = _parse_supplier_notes(notes)
    contract_saved_name = parsed_existing['contract_file']
    assert contract_saved_name == '20260101_contract.pdf'
    merged = json.loads(_merge_supplier_notes_json(
        parsed_existing['notes_json'], '', 'Camp', '', '', contract_saved_name))
    assert merged['contract_file'] == '20260101_contract.pdf'
    assert merged['bed_types'] == ['King']


def test_finance_edit_json_never_drops_contract():
    notes_json = {'category': 'Camp', 'contract_file': 'old.pdf'}
    merged = json.loads(_merge_supplier_notes_json(notes_json, '', 'Camp', '', '', ''))
    assert merged['contract_file'] == 'old.pdf'


def test_finance_text_notes_are_unchanged():
    parsed = _parse_supplier_notes('Category: 5-Star\nRoom Category: Gold Room\nSome note')
    assert parsed['notes_json'] is None
    assert parsed['category'] == '5-Star'
    assert parsed['clean_notes'] == 'Some note'
