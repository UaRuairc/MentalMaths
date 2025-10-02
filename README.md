# Maths Trainer

An interactive mental maths game built in Python, currently using UI app framework [Streamlit](https://streamlit.io/).

Goal: To create an application using LLM integration, suggesting ways for the user to optimise their mental maths training

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
├── src/
│   ├── utils.py
│   │ 
│   ├── game/
│   │   ├── content/
│   │   │   ├── modifiers.py
│   │   │   ├── problem_engine.py
│   │   │   ├── problem_tagger.py
│   │   │   ├── session_tagger.py
│   │   └── gameplay/
│   │       └── game_controller.py
│   ├── ui/
│   │   ├── pages.py
│   │   ├── widgets.py
│   │   └── page_components/
│   │       ├── auth.py
│   │       ├── game.py
│   │       └── setup.py
│   ├── config/
│   │   ├── config_init.py
│   │   └── config_management.py
│   └── database/
│       ├── connection.py
│       ├── queries.py
│       ├── telemetry.py
│       └── auth/
│           └── service.py
├── .streamlit/
│   ├── config.toml     
│   └── secrets.example.toml            # Rename to secrets.toml and put Supabase secrets here 
├── frontend/                           # Build custom widget with node (see Installation)
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── CustomInput.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── webpack.config.js
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
-----------------------
## Additional Info

### <ins>database / dev platform used</ins>
We opt to use https://supabase.com/ for our dev platform, it uses postgres

See the following resources for details:

- streamlit info: https://docs.streamlit.io/develop/tutorials/databases/supabase
- supabase Auth: https://supabase.com/docs/guides/auth

## <ins>Streamlit shortfalls & workarounds</ins>

#### TL;DR: widgets can easily lose statefulness, and widget info is tied to widget states, so create a streamlit wrapper that never loses widget info

### customisation and session state preservation-- creating a wrapper for streamlit

In many ways, this repo can really be called streamlit-wrapper. Generally speaking, one should build a game backend and use streamlit as nothing more than a UI interface, or just use a different framework altogether. But I thought it would be an interesting project to build a streamlit-wrapper that integrated my personal needs into streamlit.

The wrapper mostly deals with the fact that: In Streamlit, widgets are identified by a key:value pair in the session_state & Streamlit updates the app by rerunning the entire application with an updated session state.

When streamlit reruns, if streamlit doesn't render your widget again (e.g., you reran the app and landed on a different page), it makes the widget stateless, and you lose your widget info. But
- the app state may depend on widgets that are not currently rendered
- the app state may depend on widget info beyond the value of the widget
- the app may want to mutate widgets that are not currently rendered


There are some suggested solutions by streamlit for this, see https://docs.streamlit.io/develop/concepts/multipage-apps/widgets. But none of these really met out needs. We opt for a config & widgets wrappers/management system—essentially a wrapper for streamlit.

1. We define a config dictionary that persists reruns, and that dictionary holds entries for each widget. The entry does not just store the value of the widget (like the number inside a box), but all widget args. It even holds args beyond the widget's baseline in streamlit (customise baseline widgets).
2. We create a config manager (`ConfigManager`). The config manager uses streamlit widget signatures to build a baseline config and expands the config to meet our needs. The manager then can dynamically create/mutate widgets during runtime regardless if they have ever been rendered.
3. We create a widget wrapper (`MakeWidget`). This takes a given widget config and handles the baseline widget rendering as well as any extended widget functionality.

Essentially, combining the three steps about creates a pseudo widget session state that persists reruns and extends streamlit functionality beyond baseline. It will survive streamlit updates to widgets since we directly use widget signatures when constructing the base config prior to extension.

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
