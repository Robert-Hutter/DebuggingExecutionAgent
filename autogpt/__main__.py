"""Auto-GPT: A GPT powered AI Assistant"""
import autogpt.app.cli
from autogpt.tracer import Tracer
import autogpt.debugger
from autogpt.debugger.debugger_client import AgentDebugger
from datetime import datetime

if __name__ == "__main__":
    print('Starting trace...')
    
    tracer = Tracer(run_id=datetime.now().strftime("run_%b_%d_%H-%M-%S"))
    tracer.instrument_class(AgentDebugger, name_prefix="AgentDebugger", library="autogpt.debugger")
    
    try:
        with tracer.program("entire_run", scenario="baseline"):
            autogpt.app.cli.main()
    except KeyboardInterrupt:
        raise
    finally:
        print('Saving trace...')
        tracer.restore()
        tracer.save()