using UnityEngine;

public class Workplace : MonoBehaviour
{
    [SerializeField] private OfficeChair chair;
    private AgentController owner;

    public OfficeChair Chair => chair;
    public AgentController Owner => owner;

    public void AssignOwner(AgentController agent)
    {
        owner = agent;
    }
}