from src.domain.models import DatabaseSource
from src.domain.ports import DataSourcePort
from src.infrastructure.datasus.cnes_adapter import CNESAdapter
from src.infrastructure.datasus.sia_adapter import SIAAdapter
from src.infrastructure.datasus.sih_adapter import SIHAdapter
from src.infrastructure.datasus.sim_adapter import SIMAdapter
from src.infrastructure.datasus.sinan_adapter import SINANAdapter
from src.infrastructure.datasus.sinasc_adapter import SINASCAdapter

ADAPTER_MAP: dict[DatabaseSource, type[DataSourcePort]] = {
    DatabaseSource.SIH: SIHAdapter,
    DatabaseSource.SIM: SIMAdapter,
    DatabaseSource.SINASC: SINASCAdapter,
    DatabaseSource.SINAN: SINANAdapter,
    DatabaseSource.SIA: SIAAdapter,
    DatabaseSource.CNES: CNESAdapter,
}


def create_adapter(source: DatabaseSource) -> DataSourcePort:
    """Factory: create and load the adapter for a given database source."""
    adapter_cls = ADAPTER_MAP[source]
    return adapter_cls().load()
