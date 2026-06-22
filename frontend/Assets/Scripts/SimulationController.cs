using System;
using System.Collections.Generic;
using UnityEngine;
using Simulation.Network;

public class SimulationController : MonoBehaviour
{
    [SerializeField] private GameObject agentPrefab;
    [SerializeField] private GameObject receptionistPrefab;
    [SerializeField] private Transform[] spawnPoints;
    [SerializeField] private int agentCount = 3;

    private System.Collections.IEnumerator Start()
    {
        while (!WebSocketClientManager.Instance.IsConnected)
        {
            yield return null;
        }
        InitializeEnvironment();
    }

    private void InitializeEnvironment()
    {
        List<AgentInitInfo> agentInfos = new List<AgentInitInfo>();

        for (int i = 0; i < agentCount; i++)
        {
            Transform spawnPoint = spawnPoints[i % spawnPoints.Length];
            GameObject agentObj = Instantiate(agentPrefab, spawnPoint.position, spawnPoint.rotation);
            
            SimulationEntity entity = agentObj.GetComponent<SimulationEntity>();
            AgentController controller = agentObj.GetComponent<AgentController>();
            
            string agentId = "agent_" + i;
            entity.OverrideIdentifier(agentId);

            AgentInitInfo info = new AgentInitInfo();
            info.agentId = agentId;

            if (i == 0)
            {
                controller.SetBoss(true);
                info.role = "Boss";
                info.assignedChairId = "boss_chair";
            }
            else
            {
                controller.SetBoss(false);
                info.role = "Worker";
                info.assignedChairId = "office_chair_" + i;
            }
            agentInfos.Add(info);
        }

        Transform recSpawn = spawnPoints[0];
        GameObject recObj = Instantiate(receptionistPrefab, recSpawn.position, recSpawn.rotation);
        
        SimulationEntity recEntity = recObj.GetComponent<SimulationEntity>();
        recEntity.OverrideIdentifier("agent_reception");

        AgentController recController = recObj.GetComponent<AgentController>();
        if (recController != null)
        {
            recController.SetAIControlled(false);
        }

        List<string> zones = new List<string> 
        { 
            "chill_0", "chill_1", "chill_2", 
            "toilet_0", "toilet_1", 
            "boss_chair"
        };

        UnityEventRequest<InitializationData> startEvent = new UnityEventRequest<InitializationData>();
        startEvent.type = "daystarted";
        startEvent.agent_id = "system";
        startEvent.timestamp = DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
        startEvent.data = new InitializationData { agents = agentInfos, zones = zones };

        string json = JsonUtility.ToJson(startEvent);
        WebSocketClientManager.Instance.SendMessageToServer(json);

        StartCoroutine(RunReceptionist(recObj));
    }

    private System.Collections.IEnumerator RunReceptionist(GameObject receptionist)
    {
        AgentController controller = receptionist.GetComponent<AgentController>();
        SimulationEntity chairEntity = SimulationRegistry.GetEntity("reception_chair");
        
        while (chairEntity == null)
        {
            chairEntity = SimulationRegistry.GetEntity("reception_chair");
            yield return null;
        }

        IInteractable interactable = chairEntity.GetComponent<IInteractable>();
        TargetPose pose = interactable.Reserve(controller);
        yield return StartCoroutine(controller.MoveToDestination(pose.Position));
        controller.Interact(interactable, chairEntity);
    }
}