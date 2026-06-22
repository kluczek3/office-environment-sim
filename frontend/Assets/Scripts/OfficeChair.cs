using System.Collections;
using UnityEngine;

public class OfficeChair : MonoBehaviour, IInteractable
{
    [SerializeField] private Transform approachPoint;
    [SerializeField] private Transform sitPoint;
    [SerializeField] private Transform chairMesh;
    
    [SerializeField] private float slideDistance = 0.6f;
    [SerializeField] private float slideSpeed = 3.0f;
    [SerializeField] private float sitAnimationDuration = 1.33f;
    [SerializeField] private float standUpDelay = 1.0f;

    private AgentController occupant;
    private Vector3 originalChairWorldPos;
    private Coroutine activeSlideRoutine;

    private void Start()
    {
        if (chairMesh != null)
        {
            originalChairWorldPos = chairMesh.position;
        }
    }

    public TargetPose Reserve(AgentController agent)
    {
        return new TargetPose(approachPoint.position, approachPoint.rotation);
    }

    public string GetAnimationTrigger()
    {
        return string.Empty;
    }

    public void ExecuteAction(AgentController agent)
    {
        occupant = agent;
        agent.NavAgent.enabled = false;
        
        if (activeSlideRoutine != null) StopCoroutine(activeSlideRoutine);
        activeSlideRoutine = StartCoroutine(SitDownRoutine(agent));
    }

    public void ExitAction(AgentController agent)
    {
        if (occupant == agent)
        {
            occupant = null;
            if (activeSlideRoutine != null) StopCoroutine(activeSlideRoutine);
            activeSlideRoutine = StartCoroutine(StandUpRoutine(agent));
        }
    }

    private IEnumerator SitDownRoutine(AgentController agent)
    {
        Vector3 chairBackwards = -transform.forward;
        Vector3 pushedChairPos = originalChairWorldPos + (chairBackwards * slideDistance);
        Vector3 halfPushedChairPos = originalChairWorldPos + (chairBackwards * (slideDistance * 0.5f));

        float t = 0;
        while (t < 1.0f)
        {
            t += Time.deltaTime * slideSpeed;
            chairMesh.position = Vector3.Lerp(originalChairWorldPos, pushedChairPos, t);
            yield return null;
        }
        chairMesh.position = pushedChairPos;

        agent.transform.position = new Vector3(originalChairWorldPos.x, agent.transform.position.y, originalChairWorldPos.z);
        agent.transform.rotation = sitPoint.rotation;

        if (agent.Anim != null) agent.Anim.SetBool("Sit", true);
        
        yield return new WaitForSeconds(sitAnimationDuration);

        t = 0;
        while (t < 1.0f)
        {
            t += Time.deltaTime * slideSpeed;
            chairMesh.position = Vector3.Lerp(pushedChairPos, halfPushedChairPos, t);
            yield return null;
        }
        chairMesh.position = halfPushedChairPos;
    }

    private IEnumerator StandUpRoutine(AgentController agent)
    {
        Vector3 chairBackwards = -transform.forward;
        Vector3 pushedChairPos = originalChairWorldPos + (chairBackwards * slideDistance);
        Vector3 halfPushedChairPos = originalChairWorldPos + (chairBackwards * (slideDistance * 0.5f));
        
        float t = 0;
        while (t < 1.0f)
        {
            t += Time.deltaTime * slideSpeed;
            chairMesh.position = Vector3.Lerp(halfPushedChairPos, pushedChairPos, t);
            yield return null;
        }
        chairMesh.position = pushedChairPos;

        if (agent.Anim != null) agent.Anim.SetBool("Sit", false);
        
        yield return new WaitForSeconds(sitAnimationDuration);

        agent.transform.position = new Vector3(approachPoint.position.x, agent.transform.position.y, approachPoint.position.z);
        agent.transform.rotation = approachPoint.rotation;

        yield return new WaitForSeconds(standUpDelay);

        t = 0;
        while (t < 1.0f)
        {
            t += Time.deltaTime * slideSpeed;
            chairMesh.position = Vector3.Lerp(pushedChairPos, originalChairWorldPos, t);
            yield return null;
        }
        chairMesh.position = originalChairWorldPos;
        
        agent.NavAgent.enabled = true;
    }
}