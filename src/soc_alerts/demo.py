"""Reproducible command-line demonstration for the report's code examples."""

from datetime import datetime, timedelta, timezone

from .graph_algorithms import bellman_ford, dijkstra
from .manager import AlertManager
from .models import AlertStatus
from .sorting import insertion_sort, merge_sort


def main() -> None:
    base = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)
    # Use a fixed input timestamp so the printed demonstration is repeatable.
    manager = AlertManager(capacity=20)
    updates: list[str] = []
    manager.subscribe(lambda event: updates.append(f"{event.event_type}:{event.alert.identifier}:{event.alert.status.value}"))

    manager.add_alert("AUTH-100", "low", received_at=base, source="authentication")
    manager.add_alert("EDR-501", "critical", received_at=base + timedelta(seconds=2), source="endpoint")
    manager.add_alert("NET-204", "high", received_at=base + timedelta(seconds=3), source="network")
    manager.add_alert("SYS-010", "medium", received_at=base + timedelta(seconds=4), source="server")

    print("PROCESSING ORDER")
    # The manager always drains priority work before the routine FIFO path.
    while True:
        try:
            alert = manager.process_next()
        except IndexError:
            break
        print(f"{alert.identifier:8} | {alert.severity.name:8} | {alert.status.value}")
        manager.update_status(alert.identifier, AlertStatus.RESOLVED)

    print("\nANALYST LIFO HISTORY")
    manager.record_analyst_action("acknowledge AUTH-100")
    manager.record_analyst_action("assign EDR-501")
    print(manager.undo_last_action())
    print(manager.undo_last_action())

    print("\nREAL-TIME EVENTS")
    for update in updates[:4]:
        print(update)
    print(f"event_count={len(updates)}")

    sample = [9, 3, 7, 1, 4]
    insertion = sample.copy()
    insertion_sort(insertion)
    print("\nSORTING")
    print(f"insertion_sort={insertion}")
    print(f"merge_sort={merge_sort(sample)}")

    network = {
        "sensor": [("switch", 4), ("gateway", 2)],
        "switch": [("server", 5)],
        "gateway": [("switch", 1), ("server", 8)],
        "server": [],
    }
    print("\nNETWORK SHORTEST PATH")
    print(f"dijkstra_sensor_to_server={dijkstra(network, 'sensor')['server']:.0f}")
    print(f"bellman_ford_sensor_to_server={bellman_ford(network, 'sensor')['server']:.0f}")


if __name__ == "__main__":
    main()
