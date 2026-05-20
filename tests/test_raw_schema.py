# -*- coding: utf-8 -*-

from src.fundamental_skill.raw_schema import (
    BasicInfoInput,
    NormalizedFundamentalInput,
    RawBlockStatus,
)


def test_normalized_raw_schema_can_dump_json():
    item = NormalizedFundamentalInput(
        stock_code="000426",
        stock_name="兴业银锡",
        generated_at="2026-05-15T10:00:00",
        data_cutoff=None,
        basic_info=BasicInfoInput(stock_code="000426", stock_name="兴业银锡", market="sz"),
        raw_blocks={"basic_info": []},
        block_status=[
            RawBlockStatus(
                block_name="basic_info",
                source_name="mock",
                success=True,
                row_count=0,
                latest_period=None,
                fetched_at="2026-05-15T10:00:00",
                error_message=None,
            )
        ],
        data_sources=[],
        missing_fields=["financial_metrics"],
        adapter_warnings=[],
    )

    assert item.schema_version == "fundamental_input.v1"
    assert item.model_dump_json()
