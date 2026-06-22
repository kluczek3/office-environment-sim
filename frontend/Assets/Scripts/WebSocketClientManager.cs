using System;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;
using Simulation.Network;

public class WebSocketClientManager : MonoBehaviour
{
    public static WebSocketClientManager Instance { get; private set; }
    public bool IsConnected => webSocket != null && webSocket.State == WebSocketState.Open;

    [SerializeField] private bool useMockData = true;
    [SerializeField] private string serverUri = "ws://127.0.0.1:8080/ws/simulation/";

    private ClientWebSocket webSocket;
    private CancellationTokenSource cts;
    private readonly Queue<string> messageQueue = new Queue<string>();
    private readonly object queueLock = new object();

    private void Awake()
    {
        Instance = this;
    }

    private void Start()
    {
        if (useMockData)
        {
            Invoke(nameof(TriggerHardcodedMock), 1.5f);
        }
    }

    private void TriggerHardcodedMock()
    {
        string mockBoss = "{\"type\":\"commands\",\"agent_id\":\"agent_0\",\"commands\":[{\"type\":\"Move\",\"target_id\":\"boss_chair_0\",\"duration\":0,\"thought\":\"Muszę przejrzeć raporty.\"},{\"type\":\"Interact\",\"target_id\":\"boss_chair_0\",\"duration\":5,\"thought\":\"Dobrze, bierzemy się do pracy.\"}]}";
        string mockWorkerChill = "{\"type\":\"commands\",\"agent_id\":\"agent_1\",\"commands\":[{\"type\":\"Move\",\"target_id\":\"chill_0_0\",\"duration\":0,\"thought\":\"Czas na chwilę przerwy.\"},{\"type\":\"Interact\",\"target_id\":\"chill_0\",\"duration\":10,\"thought\":\"Dobra ta kawa, ciekawe co u innych?\"}]}";
        string mockWorkerConf = "{\"type\":\"commands\",\"agent_id\":\"agent_2\",\"commands\":[{\"type\":\"Move\",\"target_id\":\"blackboard_0_0\",\"duration\":0,\"thought\":\"Idę zaprezentować nowy projekt.\"},{\"type\":\"Interact\",\"target_id\":\"blackboard_0\",\"duration\":15,\"thought\":\"Spójrzcie na te wykresy wzrostu!\"}]}";
        
        lock (queueLock)
        {
            messageQueue.Enqueue(mockBoss);
            messageQueue.Enqueue(mockWorkerChill);
            messageQueue.Enqueue(mockWorkerConf);
        }

        Invoke(nameof(InjectDelayedQAMock), 3f);
    }

    private void InjectDelayedQAMock()
    {
        string mockQAResponse = "{\"type\":\"qa_response\",\"agent_id\":\"agent_1\",\"answer\":\"Piję kawę w strefie chillout, raport z wczoraj już wysłany!\",\"commands\":[]}";
        lock (queueLock)
        {
            messageQueue.Enqueue(mockQAResponse);
        }
    }

    public async Task ConnectAsync()
    {
        cts = new CancellationTokenSource();
        webSocket = new ClientWebSocket();
        try
        {
            await webSocket.ConnectAsync(new Uri(serverUri), cts.Token);
            byte[] buffer = new byte[8192];
            while (webSocket.State == WebSocketState.Open && !cts.Token.IsCancellationRequested)
            {
                var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cts.Token);
                string json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                lock (queueLock) { messageQueue.Enqueue(json); }
                Debug.Log(result);
                Debug.Log(json);
            }
        }
        catch (Exception ex) 
        { 
            Debug.LogError($"{ex.Message}"); 
        }
    }

    public async void SendMessageToServer(string json)
    {
        if (useMockData) return;

        if (webSocket == null || webSocket.State != WebSocketState.Open) return;

        try
        {
            byte[] buffer = Encoding.UTF8.GetBytes(json);
            await webSocket.SendAsync(new ArraySegment<byte>(buffer), WebSocketMessageType.Text, true, cts.Token);
        }
        catch (Exception ex)
        {
            Debug.LogError($"{ex.Message}");
        }
    }

    private void Update()
    {
        lock (queueLock)
        {
            while (messageQueue.Count > 0)
            {
                ProcessPackage(messageQueue.Dequeue());
            }
        }
    }

    private void ProcessPackage(string json)
    {
        try
        {
            BackendResponse package = JsonUtility.FromJson<BackendResponse>(json);
            if (package == null) return;
            
            if (package.type == "global_event")
            {
                foreach (var controller in FindObjectsOfType<AgentController>())
                {
                    controller.ForceInterruptAndRedirect();
                }
                return;
            }

            if (package.type == "qa_response")
            {
                if (QAInterfaceManager.Instance != null)
                {
                    QAInterfaceManager.Instance.ReceiveAnswer(package.agent_id, package.answer);
                }
                return;
            }

            SimulationEntity agentEntity = SimulationRegistry.GetEntity(package.agent_id);
            if (agentEntity == null) return;

            AgentController controller1 = agentEntity.GetComponent<AgentController>();
            if (controller1 == null) return;

            if (package.commands != null && package.commands.Count > 0)
                controller1.ReceiveCommands(package.commands);
        }
        catch (Exception ex) 
        { 
            Debug.LogError($"{ex.Message}"); 
        }
    }
}