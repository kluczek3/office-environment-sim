using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(BoxCollider))]
[RequireComponent(typeof(Rigidbody))]
public class ConferenceRoomController : MonoBehaviour
{
    public string zoneId;
    public List<AgentController> PresentAgents { get; private set; } = new List<AgentController>();
    public AgentController CurrentPresenter { get; private set; }

    private void Awake()
    {
        Rigidbody rb = GetComponent<Rigidbody>();
        rb.isKinematic = true;
        rb.useGravity = false;
    }

    private void OnTriggerEnter(Collider other)
    {
        AgentController agent = other.GetComponentInParent<AgentController>();
        if (agent != null && !PresentAgents.Contains(agent))
        {
            PresentAgents.Add(agent);
        }
    }

    private void OnTriggerExit(Collider other)
    {
        AgentController agent = other.GetComponentInParent<AgentController>();
        if (agent != null && PresentAgents.Contains(agent))
        {
            PresentAgents.Remove(agent);
            if (CurrentPresenter == agent)
            {
                EndPresentation();
            }
        }
    }

    public void StartPresentation(AgentController presenter)
    {
        if (PresentAgents.Contains(presenter))
        {
            CurrentPresenter = presenter;
        }
    }

    public void EndPresentation()
    {
        CurrentPresenter = null;
    }
}