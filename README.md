# Maths Trainer


An interactive mental maths game built in Python, currently using UI app framework [Streamlit](https://streamlit.io/).

Goal: To get to the heart of what improves mental arithmetic, and to build a trainer that puts it into practice with the help of LLM integration.

-----------------------

# App
  `app.py` navigates between three screens: **Setup**, **Game** and **Stats**
    
Progress:
- [x] Foundations: problem engine, ui, custom widgets, and functional game mode
- [x] Switch to a single-source-of-truth config wrapper & multipage app structure
- [x] Authentication & PostgreSQL Supabase integration
- [x] Record meaningful analytics for user development
- [x] Switch to event-driven game flow
- [x] Basic data queries/analysis on historical user data
- [x] Develop a problem-tagging framework
- [x] Develop a Modifier framework

Short-term To-do's:

- [ ] Build statistics dashboard / post-game screen
- [ ] Design experiments to be used alongside LLMs to see if the data generated is sufficient.


-----------------------
## Project Structure
```
MentalMaths/
├── app.py
├── page_navigation.py
├── requirements.txt
├── README.md
├── pages/                              # keep this folder in the root
│   ├── 1_setup_screen.py
│   ├── 2_stats_screen.py
│   └── game_screen.py
│ 
├── src/
│   ├── utils.py
│   ├── config/
│   │   └── config_init.py
│   │
│   ├── game/
│   │   ├── content/
│   │   │   ├── modifiers.py
│   │   │   ├── problem_engine.py
│   │   │   ├── problem_tagger.py
│   │   │   ├── session_tagger.py
│   │   │
│   │   └── gameplay/
│   │       └── game_controller.py
│   │
│   ├── ui/
│   │   ├── pages.py
│   │   ├── page_components/
│   │   │   ├── auth.py
│   │   │   ├── game.py
│   │   │   └── setup.py
│   │   │
│   │   └── widgets/
│   │       ├── adapters.py
│   │       ├── config.py
│   │       ├── registry.py
│   │       └── widgets.py
│   │ 
│   ├── analytics/
│   │   ├── core.py
│   │   └── visualisation.py  
│   │ 
│   └── database/
│       ├── connection.py
│       ├── queries.py
│       ├── telemetry.py
│       └── auth/
│           └── service.py
│   
├── .streamlit/
│   ├── config.toml     
│   └── secrets.example.toml            # Rename to secrets.toml and put Supabase secrets here 
│
├── frontend/                           # Build custom widget with node (see Installation)
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── CustomInput.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── webpack.config.js
│
├── tests/
│   ├── test_mod_pos_answers_only.py
│   ├── test_problem_components.py
│   ├── test_problem_generation.py
│   └── utils.py
```

-----------------------
## Installation


#### clone repo into desired location
```powershell
cd <desired directory>
git clone https://github.com/UaRuairc/MentalMaths.git
```
#### create and activate virtual environment in MentalMaths directory
```powershell
cd MentalMaths
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### install requirements in MentalMaths directory
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

#### install Node and build in MentalMaths/frontend directory
```powershell
cd frontend
npm install
npm run build
cd ..
```

#### run app from MentalMaths directory
```powershell
python -m streamlit run .\app.py --server.address localhost
```

#### Supabase:
Supabase is not required to run the project. But it is easy to setup, especially with the 

-----------------------
## Additional Info

### <ins>database / dev platform used</ins>
We opt to use https://supabase.com/ for our dev platform, it uses postgres

See the following resources for details:

- streamlit info: https://docs.streamlit.io/develop/tutorials/databases/supabase
- supabase Auth: https://supabase.com/docs/guides/auth

## <ins>Streamlit shortfalls & workarounds</ins>

#### TL;DR: widgets can easily lose statefulness, and widget info is tied to widget states, so create a streamlit wrapper that maintains all widget information.

### Motivation:

I thought it would be an interesting project to build a streamlit-wrapper that integrated my personal needs into streamlit and build a mental mathematics game. In many ways, this repo can really be called streamlit-wrapper. 

The wrapper mostly deals with the fact that: In Streamlit, widgets are identified by a key:value pair in the session_state & Streamlit updates the app by rerunning the entire application with an updated session state.

When streamlit reruns, if streamlit doesn't render your widget again (e.g., you reran the app and landed on a different page), it makes the widget stateless, and you lose your widget info. But the app state may:
- depend on the details of widgets beyond a single return `value`
- depend on the details of widgets that are no longer rendered
- want to mutate widgets that are not currently rendered (in preparation for their next render)


There are some suggested solutions by streamlit for this, see https://docs.streamlit.io/develop/concepts/multipage-apps/widgets. But none of these really met out needs. We opt for a config & widgets wrappers/management system—essentially a wrapper for streamlit.

To register widgets, we created a `WidgetRegistry` that handles widget registration.

"Widget registration" (which is done via calling `WidgetRegistry.register(widget_name, widget_category, **overrides)`) amounts to creating a `WidgetConfig` object and then storing this object in a master `config`. The master `config` is stored in `st.session_state["config"]`. A particular widget's config is then stored at 

```
st.session_state["config"][category][name]
```

As for the `WidgetConfig` object, it is responsible for:

1. **Framework compatability**:

    `WidgetConfig` detects the framework (e.g, streamlit number_input_box vs custom-made game_input_box), then guarantees (via introspection) that the correct widget is made and that the config contains all parameters necessary at render time to ensure compatability.

2. **Extension**

    After building a base config, `WidgetConfig` overrides and extends this baseline config, assuming the user provides overrides.

3. **Mutation**

    One can mutate a `WidgetConfig` via `.update()`, for example.


At rendering time, an `Adapter` interfaces between the `WidgetConfig` object and streamlit. The `StreamlitWidgetAdapter` is used for typical streamlit widgets, while `CustomWidgetAdapter` is used for our React widget. 

The adapter handles:

1. **Rendering**:

   The adapter determines which parameters are needed for rendering. It also ensures that any dynamic parameters are resolved prior to rendering.

2. **Return values**:

    The adapter handles how the widget returns a value.

3. **synchronisation:**

    The adapter ensures the widget and widget_config are synchronised at all times, via `.initialise()` and `.sync()`. 

    The first, `.initialise()`, ensures the widgets initial value sources it's truth from the widget_config. The second, `Adapter.sync()`, ensures that any mutation to a widget on streamlit's end immediately updates the widget_config.


Essentially, this ensures a single source of truth for a widget state that persists reruns and extends functionality beyond baseline. One can mutate or query a widget without needing to be on the page it was last rendered, or without it even being rendered. It preserves all widget details (beyond just the _framework_return_value) when switching pages. This has the added benefit of allowing us to save widget settings, and easily load them into the application.

### widget on_change effects

I wanted a widget that detects the key strokes of a user immediately for maths speed-drills. However, Streamlit input widgets sync to Enter/Blur HTML events (the user literally has to press Enter for the app to detect the input).

There are custom community-made components update on key press, but they do not allow mutation of the actual widget itself (if the user gets the answer right, I want to empty the box instantly via the application, I dont want the user to have to press backspace). Destroying/Creating a new widget also causes weird UI artefacts, so that is not a viable option if the box is jumping around giving the user nausea (streamlit containers do not solve this problem).

Thus, `frontend/src/CustomInput.tsx` was built:
`CustomInput.tsx` is a React component that takes as argument:
```
custom_input(
        key: str,
        correct_answer: str,
        problem_id: int,
    ) -> [user_response, problem_id, keystroke_sequence, keystroke_count]
```

The component judges if the answer is correct and resets the box (this had to be done due to desync issues between streamlit re-runs and the React component). It also records keystrokes, timings, and keystroke sequences for performance analytics.
