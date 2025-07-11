# Maths Trainer

An interactive mental maths game built in Python, currently using UI app framework [Streamlit](https://streamlit.io/).

Goal: To create an application using LLM integration, suggesting ways for the user to optimise their mental maths training

### App
  `app.py` currently has three screens: 
  1. **Setup** (WIP) – choose game settings
  2. **Game** (WIP) – play the game
  3. **Stats** (WIP) – empty (soon: show user statistics and offer advice on improving)


## Project Structure
```
MentalMaths/
├── pages/
│   ├── 1_setup_screen.py
│   ├── 2_stats_screen.py
│   ├── game_screen.py
├── src/
│   ├── problem_engine.py
│   ├── problem_generation.py
│   ├── state_management.py
│   ├── ui/
│   │   ├── pages_ui.py
│   │   ├── widgets.py
│   ├── utils.py
├── frontend/
│   ├── package.json
│   ├── public/
│   │   ├── index.html
│   ├── src/
│   │   ├── CustomInput.tsx
│   │   ├── index.tsx
│   ├── tsconfig.json
│   ├── webpack.config.js
├── .streamlit/
│   ├── config.toml
├── app.py
├── page_navigation.py
├── requirements.txt
```


## Installation 

#### clone repo
```powershell
git clone https://github.com/UaRuairc/MentalMaths.git
```
#### create and activate virtual environment
```powershell
cd MentalMaths
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### install requirements
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

#### install Node and build
```powershell
cd MentalMaths
npm install
npm run build
cd ..
```

#### run app
```powershell
python -m streamlit run .\app.py --server.address localhost
```

## Additional Info



Streamlit’s built-in `st.text_input` only syncs on “change” events (e.g. Enter or blur), thus the user entering an answer does NOT count as a on_change event, they must hit enter. We want an input component that can be cleared when the user inputs the correct answer, so the user does not have to manually delete their own input.

We tried the community `st_keyup` component, but `st_keyup` only holds the last committed value thus setting `value=""` does not clear the box on demand, one cannot access and modify the internal value streamlit displays without rewriting the component.

Rather than switch UI framework, to deliver keystroke-level interaction and instant clearing on a correct answer, `frontend/src/CustomInput.tsx` was built:  
 - A React component that takes `value=correctAnswer` and clears input upon user correctly answering the problem. The component judges if the answer is correct and resets the box (this had to be done due to desync issues between streamlit re-runs and the React component) 

More functionality (e.g., UI, stat tracking, and game modes) will be added soon.
May switch to an alternate UI framework, but Streamlit allows for easy data presentation.
