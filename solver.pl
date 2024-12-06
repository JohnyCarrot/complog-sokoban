
is_subset([],_).
is_subset([X|Xs],Y) :- %X je prvý vybraný prvok, Xs je zbytok (   zoznam ostávajúci ) 
    member(X,Y),
    is_subset(Xs,Y).


% Riešič
solve(State, Goal, Plan, Plan, Plan_lenght) :- is_subset(Goal,State).
solve(State, Goal, Sofar, Plan,s(N)) :-	
	opn(Op, Precons, Add, Delete), % get first operator
	is_subset(Precons, State), % check preconditions hold
	subtract(State, Delete, Remainder), % delete old facts; 1. argument z čoho, 2. čo ods..
	append(Add, Remainder, NewState), % add new facts
	append(Sofar, [Op], NewSofar), % add new operator
	solve(NewState, Goal, NewSofar, Plan, N). % recurse

spustac(InitialState,FinalState,Plan, N):- solve(InitialState, %Tu končí počiaročný stav
  FinalState, % Tu končí konečný stav
  [], Plan, % Prázdny plán, konečný plán v "Plan"
  N   %Max Dlžka plánu              
                   ).



% Akcie
opn( go(X,Y), % name
  [at(monkey,X),on(monkey,floor)], % preconditions
  [at(monkey,Y)], % add list
  [at(monkey,X)] ). % delete list

opn( push(box,X,Y), % name
  [at(monkey,X),on(monkey,floor),at(box,X),on(box,floor)], % preconditions
  [at(monkey,Y),at(box,Y) ], % add list
  [at(monkey,X),at(box,X)] ). % delete list

opn( climb_on(box), % name
  [at(monkey,X),on(monkey,floor),at(box,X),on(box,floor)], % preconditions
  [on(monkey,box) ], % add list
  [on(monkey,floor)] ). % delete list

opn( grab(bananas) , % name
  [on(monkey,box) ,at(box,X),at(bananas,X),status(bananas,hanging)], % preconditions
  [status(bananas,grabbed)], % add list
  [status(bananas,hanging)] ). % delete list








