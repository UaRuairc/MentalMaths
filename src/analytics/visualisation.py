import pandas as pd
import altair as alt
import streamlit as st

def interactive_timeline(problem_data: pd.DataFrame, input_colour="steelblue", del_colour="red"):

    # (WIP) to do:
    # make it problem-type agnostic
    # need to have the zoom reset when selecting new point
    # better way of dealing with very close ticks other than zoom
    # some LLM analysis that identifies strength/weaknesses
    # allow user (or the LLM) to select a subset of problems and create a new game session for targeted practice

    problem_data["problem_id"] += 1 # start at 1 instead of 0
    problem_data["keystrokes"] = problem_data["keystroke_sequence"].apply(
        lambda x: ["⌫" if pair.get("key") == "Backspace" else pair.get("key") for pair in x]
    )
    problem_data["timings"] = problem_data["keystroke_sequence"].apply(
        lambda x: [pair.get("timestamp") - x[0]["timestamp"] for pair in x] # normalise so that first timestamp is 0
    )
    problem_data["problem_string"] = problem_data.apply(
        lambda x: str(x["left_operand"]) + " + " + str(x["right_operand"]) + " = " + str(x["answer"]), axis=1
    )


    timeline_data = []
    for _, row in problem_data.iterrows():
        for idx, (key, t) in enumerate(zip(row["keystrokes"], row["timings"])):
            timeline_data.append({
                "problem_id": row["problem_id"],
                "key": key, # prob should use better naming here
                "t": t,
                "height_offset": "0" if key == "⌫" else "1",
                "problem_string": row["problem_string"],
            })
    timeline_df = pd.DataFrame(timeline_data)

    main_chart_base = (
        alt.Chart(problem_data)
        .encode(
            x=alt.X("problem_id:Q", title="Problem #"),
            y=alt.Y("answer_ms:Q", title="Answer time (ms)"),
            tooltip=["problem_id:Q", "answer_ms:Q", "problem_string:N", "keystrokes:N"],
        )
    )

    sel = alt.selection_point(
        fields=["problem_id"],
        on="click",
        value=[{"problem_id": 1}],  # reminder, needs to be list of dicts even if just 1 val..
        nearest=True,
        clear=False,
    )

    main_chart_line_layer = main_chart_base.mark_line()
    main_chart_points_layer = main_chart_base.mark_point(filled=True, size=200)
    main_chart_points_layer = main_chart_points_layer.add_params(sel).encode(
        color=alt.condition(sel, alt.value("steelblue"), alt.value("lightgray"), legend=None)
    )

    main_chart = alt.layer(main_chart_line_layer, main_chart_points_layer).properties(width=700)

    # want a secondary chart that acts as an input timeline, with deletions ⌫ to be above tick, and numbers to be below the tick.
    # need a tick layer and a text layer.
    #                                           ⌫
    #       |           |           |           |           |
    #       1           2           8                       7
    #
    #

    text_size, tick_size, tick_width, extra_space = 14, 30, 4, 20
    gap = tick_size + 4 * text_size + extra_space
    secondary_chart_height = gap + extra_space

    mid = secondary_chart_height / 2
    mid_offset = gap / 2
    del_pos = mid - mid_offset  # will set y=alt.value(0) to anchor to top, thus minus here instead of plus
    key_pos = mid + mid_offset

    zoom_x = alt.selection_interval(encodings=['x'], bind='scales')
    secondary_chart_base = (alt.Chart(timeline_df)
        .transform_calculate(type="datum.key == '⌫' ? 'Delete' : 'Input'")  # encode key presses as deletions or text input
        .encode(
            x=alt.X(
                shorthand="t:Q",
                title="time (ms)",
                scale=alt.Scale(nice=False, zero=False, padding=tick_width),
                axis=alt.Axis(labelExpr="datum.value < 0 ? '' : datum.label") # this just suppresses showing negatives when scrolling out
            ),
            color=alt.Color(shorthand="type:N", scale=alt.Scale(domain=["Input", "Delete"], range=[input_colour, del_colour]),
                            legend=None),
            tooltip=alt.value(None)
        )
    )
    secondary_chart_text_layer = (secondary_chart_base
        .mark_text(size=text_size, color="steelblue")
        .encode(
            y=alt.value(0),
            yOffset=alt.YOffset("height_offset:N", scale=alt.Scale(domain=["0", "1"], range=[del_pos, key_pos])),
            text="key:N",
        )
    )
    secondary_chart_tick_layer = secondary_chart_base.mark_tick(size=tick_size, thickness=tick_width, color="steelblue")

    inner_timeline = (
        (secondary_chart_text_layer + secondary_chart_tick_layer)
        .transform_filter(sel)
        .add_params(zoom_x)
        .properties(
            width=700,
            height=secondary_chart_height,
        )
    )

    secondary_chart = (inner_timeline # until I figure out how to add a dynamic title, will just use a facet...
        .facet(
            column=alt.Column(
                shorthand="problem_string:N",
                header=alt.Header(
                    title=None,
                    labelFont="monospace",
                    labelFontSize=text_size + 2,
                    labelPadding=8,
                    labelOrient="top"
                )
            ),
            spacing=2
        )
    )

    final = alt.vconcat(main_chart, secondary_chart, spacing=50)
    st.altair_chart(final, use_container_width=False)