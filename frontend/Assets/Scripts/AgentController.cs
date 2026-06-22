using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;
using Simulation.Network;

[RequireComponent(typeof(NavMeshAgent))]
public class AgentController : MonoBehaviour
{
    [SerializeField] private Animator anim;
    [SerializeField] private float walkSpeed = 1.5f;
    [SerializeField] private float rotationSpeed = 8.0f;
    [SerializeField] private bool isAIControlled = true;

    public NavMeshAgent NavAgent { get; private set; }
    public Animator Anim => anim;
    public bool IsBoss { get; private set; }
    
    private IInteractable currentInteractable;
    private Coroutine currentCommandRoutine;
    private Rigidbody rb;
    private AgentUIController uiController;
    private SimulationEntity myEntity;
    private Queue<NetworkCommand> commandQueue = new Queue<NetworkCommand>();
    private bool isExecuting = false;
    private bool initialDelayPassed = false;
    private String previousEntity = "";

    private void Awake()
    {
        NavAgent = GetComponent<NavMeshAgent>();
        rb = GetComponent<Rigidbody>();
        uiController = GetComponent<AgentUIController>();
        myEntity = GetComponent<SimulationEntity>();

        NavAgent.speed = walkSpeed;
        NavAgent.angularSpeed = 0; 
        NavAgent.updateRotation = false;
        NavAgent.obstacleAvoidanceType = ObstacleAvoidanceType.NoObstacleAvoidance;
    }

    private void Start()
    {
        if (isAIControlled)
        {
            StartCoroutine(InitialDelayRoutine());
        }
    }

    public void SetAIControlled(bool state)
    {
        isAIControlled = state;
    }

    private IEnumerator InitialDelayRoutine()
    {
        yield return new WaitForSeconds(5.0f);
        initialDelayPassed = true;
        RequestNextActionsFromServer();
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
        if (!isAIControlled) return;
        FindObjectOfType<UIManager>().HideLoadingScreen();

        foreach (var cmd in commands)
        {
            commandQueue.Enqueue(cmd);
        }

        if (!isExecuting)
        {
            if (currentCommandRoutine != null)
            {
                StopCoroutine(currentCommandRoutine);
            }
            currentCommandRoutine = StartCoroutine(ExecuteCommands());
        }
    }

    public void ForceInterruptAndRedirect()
    {
        if (currentCommandRoutine != null)
        {
            StopCoroutine(currentCommandRoutine);
            currentCommandRoutine = null;
        }

        commandQueue.Clear();

        if (currentInteractable != null)
        {
            currentInteractable.ExitAction(this);
            currentInteractable = null;
            if (rb != null) rb.detectCollisions = true;
        }

        if (NavAgent.enabled)
        {
            NavAgent.ResetPath();
            NavAgent.velocity = Vector3.zero;
        }

        if (Anim != null && Anim.runtimeAnimatorController != null)
        {
            Anim.SetFloat("Speed", 0f);
        }

        isExecuting = false;
        previousEntity = ""; 
        
        RequestNextActionsFromServer();
    }

    private IEnumerator ExecuteCommands()
    {
        isExecuting = true;

        while (commandQueue.Count > 0)
        {
            NetworkCommand cmd = commandQueue.Dequeue();

            if (!string.IsNullOrEmpty(cmd.thought) && uiController != null)
                uiController.ShowThought(cmd.thought);

            SimulationEntity targetEntity = null;
            if (!string.IsNullOrEmpty(cmd.target_id))
            {
                targetEntity = SimulationRegistry.GetEntity(cmd.target_id);
            }

            if (cmd.type == "Interact" && targetEntity != null && previousEntity != targetEntity.UniqueIdentifier)
            {
                previousEntity = targetEntity.UniqueIdentifier;
                IInteractable interactable = targetEntity.GetComponent<IInteractable>();
                if (interactable != null)
                {
                    TargetPose targetPose = interactable.Reserve(this);
                    yield return StartCoroutine(MoveToDestination(targetPose.Position));
                    Interact(interactable, targetEntity);
                    
                    if (cmd.duration > 0)
                    {
                        yield return new WaitForSeconds(cmd.duration * TimeManager.Instance.TimeScale);
                    }
                }
            }
            else
            {
                float waitDuration = cmd.duration > 0 ? cmd.duration : 1.0f;
                yield return new WaitForSeconds(waitDuration * TimeManager.Instance.TimeScale);
            }
        }

        isExecuting = false;
        RequestNextActionsFromServer();
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
        if (!NavAgent.enabled) NavAgent.enabled = true;
        NavAgent.isStopped = false;
        NavAgent.SetDestination(destination);
        
        yield return new WaitUntil(() => !NavAgent.pathPending);

        if (NavAgent.pathStatus == NavMeshPathStatus.PathInvalid || NavAgent.pathStatus == NavMeshPathStatus.PathPartial)
        {
            NavAgent.ResetPath();
            yield break;
        }

        float maxMovementTime = 60.0f;
        float currentMovementTimer = 0f;
        Vector3 lastPosition = transform.position;
        float stuckTimer = 0f;

        while (NavAgent.remainingDistance > NavAgent.stoppingDistance)
        {
            currentMovementTimer += Time.deltaTime;
            stuckTimer += Time.deltaTime;

            if (stuckTimer >= 10.0f)
            {
                if (Vector3.Distance(transform.position, lastPosition) < 0.05f)
                {
                    Debug.LogWarning($"[TIMEOUT] Agent {gameObject.name} utknął w miejscu.");
                    NavAgent.ResetPath();
                    yield break;
                }
                lastPosition = transform.position;
                stuckTimer = 0f;
            }

            if (currentMovementTimer >= maxMovementTime)
            {
                Debug.LogWarning($"[TIMEOUT] Agent {gameObject.name} przekroczył czas na dotarcie.");
                NavAgent.ResetPath();
                yield break;
            }

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
        }
    }

    private void RequestNextActionsFromServer()
    {
        if (!isAIControlled) return;
        if (myEntity == null || string.IsNullOrEmpty(myEntity.UniqueIdentifier)) return;

        string currentLocation = "spawn_point"; 

        if (currentInteractable != null && currentInteractable is MonoBehaviour mb)
        {
            SimulationEntity ent = mb.GetComponent<SimulationEntity>();
            if (ent != null) 
            {
                currentLocation = ent.UniqueIdentifier;
            }
        }

        string currentTimeString = TimeManager.Instance != null ? TimeManager.Instance.GetFormattedTime() : "09:00";

        var requestData = new ActionRequestData
        {
            current_location = currentLocation,
            current_time = currentTimeString
        };

        var requestPayload = new UnityEventRequest<ActionRequestData>
        {
            type = "commands", 
            agent_id = myEntity.UniqueIdentifier,
            timestamp = System.DateTime.UtcNow.Subtract(new System.DateTime(1970, 1, 1)).TotalSeconds,
            data = requestData
        };

        string json = JsonUtility.ToJson(requestPayload);
        WebSocketClientManager.Instance.SendMessageToServer(json);
    }
}