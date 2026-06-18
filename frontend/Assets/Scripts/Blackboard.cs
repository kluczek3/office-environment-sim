using UnityEngine;

public class Blackboard : MonoBehaviour, IInteractable
{
    [SerializeField] private Transform presentationPoint;
    [SerializeField] private ConferenceRoomController assignedRoom;
    
    private AgentController presenter;

    public string ZoneId => assignedRoom != null ? assignedRoom.zoneId : string.Empty;

    public TargetPose Reserve(AgentController agent)
    {
        return new TargetPose(presentationPoint.position, presentationPoint.rotation);
    }

    public string GetAnimationTrigger() => string.Empty;

    public void ExecuteAction(AgentController agent)
    {
        presenter = agent;
        agent.NavAgent.enabled = false;
        agent.transform.position = presentationPoint.position;
        agent.transform.rotation = presentationPoint.rotation;
        
        if (agent.Anim != null) 
        {
            agent.Anim.SetBool("Talk", true);
        }

        if (assignedRoom != null)
        {
            assignedRoom.StartPresentation(presenter);
        }
    }

    public void ExitAction(AgentController agent)
    {
        if (agent.Anim != null) agent.Anim.SetBool("Talk", false);

        if (presenter == agent)
        {
            presenter = null;
            if (assignedRoom != null)
            {
                assignedRoom.EndPresentation();
            }
        }
        agent.NavAgent.enabled = true;
    }
}