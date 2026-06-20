using System.Collections;
using System.Collections.Generic;
using System.Net;
using UnityEngine;
using UnityEngine.AI;
using Simulation.Network;

[RequireComponent(typeof(NavMeshAgent))]
public class AgentController : MonoBehaviour
{
    [SerializeField] private Animator anim;
    [SerializeField] private float walkSpeed = 1.5f;
    [SerializeField] private float rotationSpeed = 8.0f;

    public NavMeshAgent NavAgent { get; private set; }
    public Animator Anim => anim;
    public bool IsBoss { get; private set; }
    
    private IInteractable currentInteractable;
    private Coroutine currentCommandRoutine;
    private Rigidbody rb;
    private AgentUIController uiController;
    private SimulationEntity myEntity;

    private void Awake()
    {
        NavAgent = GetComponent<NavMeshAgent>();
        rb = GetComponent<Rigidbody>();
        uiController = GetComponent<AgentUIController>();
        myEntity = GetComponent<SimulationEntity>();

        NavAgent.speed = walkSpeed;
        NavAgent.angularSpeed = 0; 
        NavAgent.updateRotation = false; 
    }

    public void SetBoss(bool bossState)
    {
        IsBoss = bossState;
    }

    private void Update()
    {
        if (NavAgent.enabled)
        {
            float currentSpeed = NavAgent.velocity.magnitude;

            if (Anim != null && Anim.runtimeAnimatorController != null)
            {
                Anim.SetFloat("Speed", currentSpeed);
            }

            if (currentSpeed > 0.1f)
            {
                Vector3 lookDirection = NavAgent.velocity.normalized;
                lookDirection.y = 0;
                Quaternion targetRotation = Quaternion.LookRotation(lookDirection);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * rotationSpeed);
            }
        }
    }

    public void ReceiveCommands(List<NetworkCommand> commands)
    {
        if (currentCommandRoutine != null)
        {
            StopCoroutine(currentCommandRoutine);
        }
        currentCommandRoutine = StartCoroutine(ExecuteCommands(commands));
    }

    private IEnumerator ExecuteCommands(List<NetworkCommand> commands)
    {
        foreach (var cmd in commands)
        {
            if (!string.IsNullOrEmpty(cmd.thought) && uiController != null)
                uiController.ShowThought(cmd.thought);
            

            SimulationEntity targetEntity = SimulationRegistry.GetEntity(cmd.target_id);

            if (cmd.type == "Move")
            {
                if (targetEntity != null) 
                    yield return StartCoroutine(MoveToDestination(targetEntity.transform.position));
            }
            else if (cmd.type == "Interact")
            {
                if (targetEntity != null)
                {
                    IInteractable interactable = targetEntity.GetComponent<IInteractable>();
                    if (interactable != null)
                    {
                        TargetPose targetPose = interactable.Reserve(this);
                        yield return StartCoroutine(MoveToDestination(targetPose.Position));
                        Interact(interactable, targetEntity);
                    }
                }
            }
            else if (cmd.type == "Wait")
                yield return new WaitForSeconds(cmd.duration);
        }
    }

    public IEnumerator MoveToDestination(Vector3 destination)
    {
        if (currentInteractable != null)
        {
            currentInteractable.ExitAction(this);
            currentInteractable = null;
            if (rb != null)
            {
                rb.detectCollisions = true;
            }
        }

        if (NavAgent.enabled) NavAgent.isStopped = false;
        NavAgent.SetDestination(destination);
        
        yield return new WaitUntil(() => !NavAgent.pathPending);

        if (NavAgent.pathStatus == NavMeshPathStatus.PathInvalid || NavAgent.pathStatus == NavMeshPathStatus.PathPartial)
        {
            NavAgent.ResetPath();
            yield break;
        }

        while (NavAgent.remainingDistance > NavAgent.stoppingDistance)
        {
            yield return null;
        }

        NavAgent.velocity = Vector3.zero;
        if (Anim != null && Anim.runtimeAnimatorController != null)
        {
            Anim.SetFloat("Speed", 0f);
        }
    }

    public void Interact(IInteractable interactable, SimulationEntity entity)
    {
        currentInteractable = interactable;
        interactable.ExecuteAction(this);

        if (entity != null)
        {
            if (entity.BaseType == "toilet")
            {
                if (rb != null)
                {
                    rb.detectCollisions = false;
                }
            }
            else if (entity.BaseType == "blackboard")
            {
            }
        }
    }
}