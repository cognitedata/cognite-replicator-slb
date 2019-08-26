import time

from cognite.client.data_classes.assets import Asset
from cognite.replicator.assets import build_asset_create, build_asset_update
from cognite.replicator.assets import find_children, create_hierarchy
from cognite.client.testing import mock_cognite_client


def test_build_asset_create():
    asset = Asset(id=3, name="holy grenade", metadata={})
    runtime = time.time() * 1000
    created = build_asset_create(asset, {}, "source_tenant", runtime, 0)
    assert "holy grenade" == created.name
    assert created.parent_id is None
    assert created.metadata
    assert "source_tenant" == created.metadata["_replicatedSource"]
    assert 3 == created.metadata["_replicatedInternalId"]

    asset = Asset(id=4, parent_id=2, name="holy grail", metadata={"_replicatedInternalId": 55})
    src_id_dst_map = {2: 5}
    second = build_asset_create(asset, src_id_dst_map, "source_tenant", runtime, 2)
    assert 5 == second.parent_id


def test_find_children():
    assets = [
        Asset(id=3, name="holy grenade", metadata={}),
        Asset(id=7, name="not holy grenade", parent_id=3, metadata={}),
        Asset(id=5, name="in-holy grenade", parent_id=7, metadata={"source": "None"}),
    ]
    parents = find_children(assets, [None])
    children1 = find_children(assets, parents)
    children2 = find_children(assets, children1)
    assert parents[0].id == 3
    assert children1[0].id == 7
    assert children2[0].id == 5
    assert children1[0].parent_id == 3
    assert children2[0].parent_id == 7


def test_build_asset_update():
    assets_src = [
        Asset(id=3, name="Dog", external_id="Woff Woff", metadata={}, description="Humans best friend"),
        Asset(id=7, name="Cat", external_id="Miau Miau", metadata={}),
        Asset(id=5, name="Cow", metadata={}),
    ]
    assets_dst = [
        Asset(id=333, name="Copy-Dog", metadata={}),
        Asset(id=777, name="Copy-Cat", parent_id=3, metadata={}),
        Asset(id=555, name="Copy-Cow", parent_id=7, metadata={"source": "None"}),
    ]
    runtime = time.time() * 1000
    dst_asset_0 = build_asset_update(assets_src[0], assets_dst[0], [], "Flying Circus", runtime, depth=1)
    dst_asset_1 = build_asset_update(assets_src[1], assets_dst[1], [], "Flying Circus", runtime, depth=1)
    dst_asset_2 = build_asset_update(assets_src[2], assets_dst[2], [], "Flying Circus", runtime, depth=1)
    assert dst_asset_0.metadata["_replicatedSource"] == "Flying Circus"
    assert dst_asset_1.metadata["_replicatedSource"] == "Flying Circus"
    assert dst_asset_2.metadata["_replicatedSource"] == "Flying Circus"
    assert dst_asset_0.metadata["_replicatedInternalId"] == assets_src[0].id
    assert dst_asset_1.metadata["_replicatedInternalId"] == assets_src[1].id
    assert dst_asset_2.metadata["_replicatedInternalId"] == assets_src[2].id
    assert dst_asset_0.description == assets_src[0].description


def test_create_hierarchy():
    with mock_cognite_client() as client:
        runtime = time.time() * 1000
        assets_src = [
            Asset(
                id=3, name="Queen", external_id="Queen in the Kingdom", metadata={}, description="Married to the King"
            ),
            Asset(id=7, name="Prince", parent_id=3, external_id="Future King", metadata={}),
            Asset(id=5, name="Princess", parent_id=3, metadata={}),
        ]
        #src_emptydst_ids = create_hierarchy(assets_src, [], "Evens Kingdom", runtime, client)
        assets_dst = [
            Asset(
                id=333,
                name="Copy-Queen",
                external_id="Queen in the Kingdom",
                metadata={"_replicatedInternalId": 3, "_replicatedTime": 1},
                description="Married to the King",
            ),
            Asset(
                id=777,
                name="Copy-Prince",
                external_id="Future King",
                metadata={"_replicatedInternalId": 7, "_replicatedTime": 1},
            ),
            Asset(id=555, name="Copy-Princess", metadata={"_replicatedInternalId": 5, "_replicatedTime": 1}),
            Asset(id=101, name="Adopted", metadata={}),
        ]

        src_dst_ids = create_hierarchy(assets_src, assets_dst, "Evens Kingdom", runtime, client)
