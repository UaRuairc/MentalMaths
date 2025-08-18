# Maths Trainer

An interactive mental maths game built in Python, currently using UI app framework [Streamlit](https://streamlit.io/).

Goal: To create an application using LLM integration, suggesting ways for the user to optimise their mental maths training

-----------------------

## App
  `app.py` navigates between three screens: **Setup**, **Game** and **Stats**

  **Status**: core problem generation, settings, ui and gameplay functional; supabase postgreSQL db integrated; core widget & config wrapper + API complete

  **In progress**: track stats in postgreSQL, additional game modes, stat dashboard and training tips

  **Immediate priority**: stable and scalable tracking of meaningful stats

-----------------------
## Project Structure
```
MentalMaths/
├── app.py
├── page_navigation.py
├── requirements.txt
├── README.md
│ 
├── pages/
│   ├── 1_setup_screen.py
│   ├── 2_stats_screen.py
│   └── game_screen.py
│ 
├── src/
│   ├── utils.py
│   │  
│   ├── config/
│   │   ├── config_init.py
│   │   └── config_management.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── events.py
│   │   └── auth/
│   │       └── service.py
│   │ 
│   ├── problem_management/
│   │   ├── problem_engine.py
│   │   └── problem_generation.py
│   │
│   ├── state_management/
│   │   └── game_state.py
│   │ 
│   └── ui/
│       ├── pages.py
│       ├── widgets.py
│       └── page_components/
│           ├── auth.py
│           ├── game.py
│           ├── setup.py
│           └── stats.py
│
├── .streamlit/
│   ├── config.toml     
│   └── secrets.example.toml            # Rename to secrets.toml and put Supabase secrets here 
│
├── frontend/                           # Build custom widget with node (see Installation)
│   ├── package.json
│   ├── tsconfig.json
│   ├── webpack.config.js
│   │
│   ├── build/
│   │   ├── CustomInput.d.ts
│   │   ├── index.d.ts
│   │   ├── index.html
│   │   ├── index.js
│   │   └── index.js.LICENSE.txt
│   │ 
│   ├── public/
│   │   └── index.html
│   │
│   └── src/
│       ├── CustomInput.tsx
│       ├── custom_range_input.tsx
│       └── index.tsx
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

### <ins>Why use a custom react component?</ins>

Streamlit’s built-in `st.text_input` only syncs on “change” events (e.g. Enter or blur), thus the user entering an answer does NOT count as a on_change event, they must hit enter or streamlit does not know they have inputted an answer. You can use some methods to deal with this, but it results in the widget being created/destroyed and it is visually unappealing. 

We want an input component that

1. immediately sends the input to streamlit on keystroke 
2. Be automatically cleared when the user inputs the correct answer, so the user does not have to manually delete their own input or press enter to type in the next answer

We tried the community `st_keyup` component, but `st_keyup` only holds the last committed value thus setting `value=""` does not clear the box on demand, one cannot access and modify the internal value streamlit displays without rewriting the component.

Rather than switch UI framework, to meet our requirements `frontend/src/CustomInput.tsx` was built:  

`CustomInput.tsx` is a React component that takes `value=correctAnswer` and clears input upon user correctly answering the problem. The component judges if the answer is correct and resets the box (this had to be done due to desync issues between streamlit re-runs and the React component) 
