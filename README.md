# Maths Trainer

An interactive, web-based mental maths game built in Python using [Streamlit](https://streamlit.io/).

Goal: To create an application using LLM integration, suggesting ways for the user to optimise their mental maths training


## Overview

- **App**  
  The main UI is in `app.py` and provides two screens:  
  1. **Setup** (WIP) – choose which operations to include, set your digit-range sliders, and pick a game duration.  
  2. **Game** (WIP) – solve as many problems as you can before the timer expires; your score updates live.


- **Helpers**  
  The core problem generator lives in `Core/simulator.py`. Currently, it produces integer addition, subtraction, multiplication, 
  and division problems with configurable digit ranges. 
  Custom widget contained in `frontend\src\CustomInput.tsx`
  Widget helpers contained in `widgets.py`



- **Custom Input Component**  
   Streamlit’s built-in `st.text_input` only syncs on “change” events (e.g. Enter or blur). We tried the community `st_keyup` component, but it only held the last committed value—setting it to `""` didn’t clear the box.  
  To deliver keystroke-level interaction and instant clearing on a correct answer, `frontend/src/CustomInput.tsx` was built:  
  - A React component that takes `value=correctAnswer` and clears input upon user correctly answering the problem.

More functionality (e.g., UI, stat tracking, and game modes) will be added soon.
May switch to an alternate UI framework, but Streamlit allows for easy data presentation.

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
streamlit run app.py
```




