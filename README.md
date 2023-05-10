Google Sheet for Solvers Comparision: https://docs.google.com/spreadsheets/d/1eHaEsVsWJSm-UYiAW34GOKpbrfaD1_RH/edit#gid=542634310

Google OR-Tool Information: https://docs.google.com/document/d/1LVDRISzdRzhyCxSj1HVn9CU5Lwqy8yoBfNTYOyEfAkM/edit?usp=sharing

### TASK

- [ ] defualt route distances
- [x] create distance matrix for case 1
  - function: asymetric/symmetric confirmation
  - function: fill nan
  - iteration for region
- [ ] create distance matrix for case 2/3
- [ ] convert ATSP to sym TSP
   - [x] read ATSP file
   - [x] make asym to sym
   - [ ] save new sym to .tsp file
- [ ] finding solver (check marks are confirmation that we can execute the code and get the acceptable results)
   - [ ] [LK-heuristic python](https://pypi.org/project/lk-heuristic) -> input: array | if we have time we might tweak code to work with ATSP
   - [ ] [LKH](https://pypi.org/project/lkh/) -> input: .atsp file | it gives route but no distance | it gives a list of [solution](https://github.com/Pratiksha100/AnalyticsProject/blob/cheewan/ResultFromLKH.md) (prom)
   - [x] [ORtools](https://developers.google.com/optimization) -> input: array
      - [ ] Theory behind this tool
   - [ ] [Concorde](https://www.math.uwaterloo.ca/tsp/concorde.html) -> input: .tsp file
- [ ] Generate Real Instances, corresponding Distance Marix (check branch 'ghozie')
- [ ] Analytics


### To Do Task for next meeting
- [ ] Revise the Google sheet solver comparision for new Alina code
- [ ] Generate the instances as provided by Rossana
- [ ] Do the experimental set up 
- [ ] Implement LKH.exe in python
