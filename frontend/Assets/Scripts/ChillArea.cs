using UnityEngine;

public class ChillArea : MonoBehaviour, IInteractable
{
    [SerializeField] private Transform centerPoint;
    [SerializeField] private float radius = 2.0f;
    [SerializeField] private ChillAreaController assignedController;

    public string ZoneId => assignedController != null ? assignedController.zoneId : string.Empty;

    public string GetAnimationTrigger() => string.Empty;

    public TargetPose Reserve(AgentController agent)
    {
        Vector2 randomCircle = Random.insideUnitCircle * radius;
        Vector3 position = centerPoint.position + new Vector3(randomCircle.x, 0, randomCircle.y);
        return new TargetPose(position, centerPoint.rotation);
    }

    public void ExecuteAction(AgentController agent)
    {
        if (agent.Anim != null) agent.Anim.SetBool("Talk", true);

        Vector3 lookDirection = centerPoint.position - agent.transform.position;
        lookDirection.y = 0;
        if (lookDirection.magnitude > 0.1f)
        {
            agent.transform.rotation = Quaternion.LookRotation(lookDirection);
        }
    }

    public void ExitAction(AgentController agent)
    {
        if (agent.Anim != null) agent.Anim.SetBool("Talk", false);
    }
}