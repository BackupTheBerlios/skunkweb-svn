# Time-stamp: <02/11/26 14:40:35 smulloni>
# $Id: dispatcher.py,v 1.7 2002/11/26 20:52:46 smulloni Exp $

from containers.fieldcontainer import FieldContainer
from form import _getname

class Goto:
    def __init__(self, formname):
        self.formname=formname
        
    def dispatch(self,
                 form,
                 state,
                 argdict,
                 formdict,
                 ns):
        form.submit(argdict)
        if form.errors:
            return form
        form.process(argdict, state, ns)
        if self.formname:
            return formdict[self.formname]

class Pop:
    def dispatch(self,
                 form,
                 state,
                 argdict,
                 formdict,
                 ns):
        form.submit(argdict)
        if form.errors:
            return form
        form.process(argdict, state, ns)
        return state.pop_form()

class Push:
    def __init__(self, formname, valid=0):
        self.formname=formname
        self.valid=valid
        
    def dispatch(self,
                 form,
                 state,
                 argdict,
                 formdict,
                 ns):
        if self.valid:
            form.submit(argdict)
            if form.errors:
                return form
        state.push_form(form)
        return formdict[self.formname]

    
class FormDispatcher:
    def __init__(self,
                 statemgr,
                 forms,
                 flowmgr=None,
                 stateVariable='_state'):
        self.forms=FieldContainer(forms,
                                  fieldmapper=_getname,
                                  storelists=0)
        self.statemgr=statemgr
        if flowmgr is None:
            flowmgr=LinearFlowManager(self.forms)
        self.flowmgr=flowmgr
        self.stateVariable=stateVariable

    def dispatch(self, argdict, ns):
        # extract the state
        statestr=argdict.get(self.stateVariable)
        if statestr:
            self.statemgr.read(statestr)
        # identify the form being submitted.
        if self.statemgr.formname:
            form=self.forms[self.statemgr.formname]
            # get the next action.
            action=self.flowmgr.next(form,
                                     self.statemgr,
                                     argdict,
                                     ns)
            # get the next form, if any
            form=action.dispatch(form,
                                 self.statemgr,
                                 argdict,
                                 self.forms,
                                 ns)
            
        # if there isn't one, return the start form.
        else:
            form=self.flowmgr.getStartForm()
            form.reset()
        if form:
            # update the state with the new form name
            self.statemgr.formname=form.name
            # set the new state in the form's stateVariable 
            form.fields[self.stateVariable].value=self.statemgr.write()
        return form
    
class LinearFlowManager(object):
    def __init__(self, formlist):
        self.formlist=formlist

    def getStartForm(self):
        return self.formlist[0]

    def next(self, form, state, argdict, ns):
        ind=self.formlist.index(form) + 1
        if ind < len(self.formlist):
            return Goto(self.formlist[ind].name)
        return Goto(None) # end
