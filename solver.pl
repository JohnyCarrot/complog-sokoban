
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
  [exist(X,Y),free(Y),at('S',X)], % preconditions | exist znamená, že Y vlastne existuje v 4roch smeroch okolo Xa dá sa z neho ísť na Y
  [free(X),at('S',Y)], % add list
  [free(Y),at('S',X)]). % delete list

  
opn(push(X, Y, Z),
    [at('S', X), at('C', Y), pushable(Y, Z), free(Z)], % Preconditions
    [at('C', Z), at('S', Y), free(X)],                          % Add list
    [at('C', Y), at('S', X), free(Z),pushable(Y, Z)]                  % Delete list
).









