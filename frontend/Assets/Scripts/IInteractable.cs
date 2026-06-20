using UnityEngine;

public interface IInteractable
{
    TargetPose Reserve(AgentController agent);
    
    string GetAnimationTrigger();
    
    void ExecuteAction(AgentController agent);
    void ExitAction(AgentController agent);
}