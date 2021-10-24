import pyhop
import json

def check_enough (state, ID, item, num):
    if getattr(state,item)[ID] >= num: return []
    return False

def produce_enough (state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
    return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method (name, rule):
    def method (state, ID):
        # your code here
        requires = rule[0]
        consumes = rule[1]
        l = []
        
        for key in requires.keys():
            l.append(('have_enough', ID, key, requires[key]))
            
        for key in consumes.keys():
            l.append(('have_enough', ID, key, consumes[key]))
        
        l.append((name, ID))
        
        return l

    return method

def declare_methods (data):
    # some recipes are faster than others for the same product even though they might require extra tools
    # sort the recipes so that faster recipes go first

    # your code here
    # hint: call make_method, then declare the method to pyhop using pyhop.declare_methods('foo', m1, m2, ..., mk)    
    
    for item in data['Recipes'].keys():
        produces = list(data['Recipes'][item]['Produces'].keys())[0]
        time = data['Recipes'][item]['Time']
        items = [(time, item)]
        
        for item2 in data['Recipes'].keys():
            produces2 = list(data['Recipes'][item2]['Produces'].keys())[0]
            if produces2 == produces and item != item2:
                time2 = data['Recipes'][item2]['Time']
                items.append((time2, item2))
        
        items = sorted(items)
        
        methods = []
        for recipe in items:
            requires = {}
            if 'Requires' in data['Recipes'][recipe[1]]:
                requires = data['Recipes'][recipe[1]]['Requires']
            consumes = {}
            if 'Consumes' in data['Recipes'][recipe[1]]:
                consumes = data['Recipes'][recipe[1]]['Consumes']
            name = 'op_'+recipe[1]
            m = make_method(name, [requires, consumes])
            m.__name__ = recipe[1]
            methods.append(m)
        
        name = 'produce_'+produces
        newList = [name] + methods
        
        pyhop.declare_methods(*newList)
        
    return           

def make_operator (rule):
    #print(rule)
    def operator (state, ID):
        # your code here
        requires = rule[0]
        consumes = rule[1]
        produces = rule[2]
        time = rule[3]
        
        # make sure all requirements are met.
        for key in requires.keys():
            if requires[key] > getattr(state, key)[ID]:
                return False
        
        # check that there is enough time
        if time > state.time[ID]:
            return False
        
        
        for key in consumes.keys():
            if consumes[key] > getattr(state, key)[ID]:
                return False
        # remove items that are consumed.
        for key in consumes.keys():
            total = getattr(state, key)[ID]
            consumed = consumes[key]
            newTotal = total - consumed
            setattr(state, key, {ID: newTotal})
        
        # add items that are created
        for key in produces.keys():
            total = getattr(state, key)[ID]
            produced = produces[key]
            newTotal = total + produced
            setattr(state, key, {ID: newTotal})
        
        state.time[ID] -= time
        
        # successful return
        return state
    
    return operator

def declare_operators (data):
    # your code here
    # hint: call make_operator, then declare the operator to pyhop using pyhop.declare_operators(o1, o2, ..., ok)
    
    for item in data['Recipes'].keys():        
        requires = {}
        consumes = {}
        # dictionary containing requirements.
        if 'Requires' in data['Recipes'][item]:
            requires = data['Recipes'][item]['Requires']
        # dictionary containing costs.
        if 'Consumes' in data['Recipes'][item]:
            consumes = data['Recipes'][item]['Consumes']
        # dictionary containing results.
        produces = data['Recipes'][item]['Produces']
        # int that represents the time for a task.
        time = data['Recipes'][item]['Time']
        
        rule = [requires, consumes, produces, time]
        
        operator = make_operator(rule)
        operator.__name__ = 'op_'+item
        
        pyhop.declare_operators(operator)
    
    return

def add_heuristic (data, ID):
    # prune search branch if heuristic() returns True
    # do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
    # e.g. def heuristic2(...); pyhop.add_check(heuristic2)
    def heuristic (state, curr_task, tasks, plan, depth, calling_stack):
        # your code here
        return False # if True, prune this branch

    pyhop.add_check(heuristic)


def set_up_state (data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}

    for item in data['Items']:
        setattr(state, item, {ID: 0})

    for item in data['Tools']:
        setattr(state, item, {ID: 0})

    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})

    return state

def set_up_goals (data, ID):
    goals = []
    for item, num in data['Goal'].items():
        goals.append(('have_enough', ID, item, num))

    return goals

if __name__ == '__main__':
    rules_filename = 'crafting.json'

    with open(rules_filename) as f:
        data = json.load(f)

    state = set_up_state(data, 'agent', time=300) # allot time here
    goals = set_up_goals(data, 'agent')

    declare_operators(data)
    declare_methods(data)
    add_heuristic(data, 'agent')

    #pyhop.print_operators()
    pyhop.print_methods()

    # Hint: verbose output can take a long time even if the solution is correct; 
    # try verbose=1 if it is taking too long
    pyhop.pyhop(state, goals, verbose=1)
    #pyhop.pyhop(state, goals, verbose=3)
    # pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
