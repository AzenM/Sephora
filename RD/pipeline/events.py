"""Build layered event log (raw + milestone events)."""

import pandas as pd


GOOD_RFM_IDS = {1, 2, 3}
LOYALTY_TIERS = ("Bronze", "Silver", "Gold")


def _clean_event_name(value: str) -> str:
    return (
        str(value)
        .lower()
        .replace("&", "and")
        .replace(" ", "_")
        .replace("/", "_")
    )


def build_event_log(df: pd.DataFrame, customers: pd.DataFrame, ticket: pd.DataFrame) -> pd.DataFrame:
    """Create a PM4PY-friendly event log with milestone events."""

    events: list[dict] = []

    for _, row in ticket.iterrows():
        channel = row.get("channel", "store")
        events.append({
            "case:concept:name": str(row["anonymized_card_code"]),
            "concept:name": f"purchase_{_clean_event_name(channel)}",
            "time:timestamp": row["date"],
            "revenue": row["revenue"],
            "discount": row.get("discount", 0),
            "channel": channel,
            "category": row.get("main_cat", "Unknown"),
            "visit_rank": row["visit_rank"],
        })

    tickets_by_customer = ticket.sort_values(["anonymized_card_code", "date", "visit_rank"])
    states_by_customer = df.sort_values(["anonymized_card_code", "transactionDate", "anonymized_Ticket_ID"])

    for customer_id, grp in tickets_by_customer.groupby("anonymized_card_code"):
        customer_key = str(customer_id)
        rows = grp.to_dict("records")
        if not rows:
            continue

        first = rows[0]
        first_category = first.get("main_cat", "Unknown")

        events.append({
            "case:concept:name": customer_key,
            "concept:name": "first_purchase",
            "time:timestamp": first["date"],
            "revenue": first["revenue"],
            "channel": first.get("channel", ""),
            "category": first_category,
            "visit_rank": 1,
            "discount": first.get("discount", 0),
        })
        events.append({
            "case:concept:name": customer_key,
            "concept:name": f"first_purchase_{_clean_event_name(first_category)}",
            "time:timestamp": first["date"],
            "revenue": first["revenue"],
            "channel": first.get("channel", ""),
            "category": first_category,
            "visit_rank": 1,
            "discount": first.get("discount", 0),
        })

        if len(rows) >= 2:
            second = rows[1]
            gap = (second["date"] - first["date"]).days
            label = "second_purchase_under_30d" if gap <= 30 else (
                "second_purchase_under_60d" if gap <= 60 else "second_purchase_late"
            )
            events.append({
                "case:concept:name": customer_key,
                "concept:name": label,
                "time:timestamp": second["date"],
                "revenue": second["revenue"],
                "channel": second.get("channel", ""),
                "category": second.get("main_cat", ""),
                "visit_rank": 2,
                "discount": second.get("discount", 0),
            })

        seen_channels: set[str] = set()
        seen_categories: set[str] = set()
        omnichannel_fired = False
        category_expansion_fired = False

        for visit in rows:
            channel = str(visit.get("channel", ""))
            category = str(visit.get("main_cat", ""))
            seen_channels.add(channel)
            seen_categories.add(category)

            if len(seen_channels) >= 2 and not omnichannel_fired:
                omnichannel_fired = True
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": "omnichannel_adoption",
                    "time:timestamp": visit["date"],
                    "revenue": 0,
                    "channel": channel,
                    "category": category,
                    "visit_rank": visit["visit_rank"],
                    "discount": 0,
                })

            if len(seen_categories) >= 3 and not category_expansion_fired:
                category_expansion_fired = True
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": "category_expansion",
                    "time:timestamp": visit["date"],
                    "revenue": 0,
                    "channel": channel,
                    "category": category,
                    "visit_rank": visit["visit_rank"],
                    "discount": 0,
                })

            if visit["revenue"] >= 150:
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": "high_basket_event",
                    "time:timestamp": visit["date"],
                    "revenue": visit["revenue"],
                    "channel": channel,
                    "category": category,
                    "visit_rank": visit["visit_rank"],
                    "discount": visit.get("discount", 0),
                })

            total_value = visit["revenue"] + visit.get("discount", 0)
            if total_value > 0 and visit.get("discount", 0) / total_value > 0.30:
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": "high_discount_purchase",
                    "time:timestamp": visit["date"],
                    "revenue": visit["revenue"],
                    "channel": channel,
                    "category": category,
                    "visit_rank": visit["visit_rank"],
                    "discount": visit.get("discount", 0),
                })

        customer_states = states_by_customer[states_by_customer["anonymized_card_code"] == customer_id]
        seen_tiers: set[str] = set()
        seen_good_rfm: set[int] = set()

        for _, state in customer_states.iterrows():
            loyalty = state.get("loyalty_label")
            rfm_id = state.get("RFM_Segment_ID")
            timestamp = state.get("transactionDate")

            if loyalty in LOYALTY_TIERS and loyalty not in seen_tiers:
                seen_tiers.add(loyalty)
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": f"{str(loyalty).lower()}_reached",
                    "time:timestamp": timestamp,
                    "revenue": 0,
                    "channel": state.get("channel_clean", ""),
                    "category": state.get("Axe_Desc", ""),
                    "visit_rank": None,
                    "discount": 0,
                })

            if pd.notna(rfm_id):
                rfm_int = int(rfm_id)
                if rfm_int in GOOD_RFM_IDS and rfm_int not in seen_good_rfm:
                    seen_good_rfm.add(rfm_int)
                    events.append({
                        "case:concept:name": customer_key,
                        "concept:name": f"moved_to_rfm_{rfm_int}",
                        "time:timestamp": timestamp,
                        "revenue": 0,
                        "channel": state.get("channel_clean", ""),
                        "category": state.get("Axe_Desc", ""),
                        "visit_rank": None,
                        "discount": 0,
                    })

        for previous_visit, current_visit in zip(rows, rows[1:]):
            gap = (current_visit["date"] - previous_visit["date"]).days
            if gap >= 60:
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": "inactivity_60d",
                    "time:timestamp": previous_visit["date"] + pd.Timedelta(days=60),
                    "revenue": 0,
                    "channel": previous_visit.get("channel", ""),
                    "category": previous_visit.get("main_cat", ""),
                    "visit_rank": previous_visit["visit_rank"],
                    "discount": 0,
                })
                events.append({
                    "case:concept:name": customer_key,
                    "concept:name": "reactivated",
                    "time:timestamp": current_visit["date"],
                    "revenue": current_visit["revenue"],
                    "channel": current_visit.get("channel", ""),
                    "category": current_visit.get("main_cat", ""),
                    "visit_rank": current_visit["visit_rank"],
                    "discount": current_visit.get("discount", 0),
                })

    customer_flags = customers[[
        "anonymized_card_code",
        "discount_ratio",
        "last_date",
        "loyalty_label",
        "rfm_label",
    ]].copy()
    customer_flags["case:concept:name"] = customer_flags["anonymized_card_code"].astype(str)

    for _, row in customer_flags.iterrows():
        if row["discount_ratio"] >= 0.30:
            events.append({
                "case:concept:name": row["case:concept:name"],
                "concept:name": "high_discount_dependency",
                "time:timestamp": row["last_date"],
                "revenue": 0,
                "discount": 0,
                "channel": "",
                "category": "",
                "visit_rank": None,
            })

    event_log = pd.DataFrame(events)
    event_log["time:timestamp"] = pd.to_datetime(event_log["time:timestamp"])
    event_log = event_log.sort_values(
        ["case:concept:name", "time:timestamp", "concept:name"]
    ).reset_index(drop=True)

    return event_log
