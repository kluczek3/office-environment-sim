using UnityEngine;
using TMPro;
using UnityEngine.UI;
using Simulation.Network;
using System;
using UnityEngine.InputSystem;

public class QAInterfaceManager : MonoBehaviour
{
    public static QAInterfaceManager Instance { get; private set; }

    [SerializeField] private GameObject qaPanel;
    [SerializeField] private TextMeshProUGUI headerText;
    [SerializeField] private TextMeshProUGUI answerText;
    [SerializeField] private TMP_InputField inputField;
    [SerializeField] private Button sendButton;
    [SerializeField] private Button closeButton;

    private string currentAgentId;
    public bool IsPanelActive = false;

    private void Awake()
    {
        Instance = this;
        qaPanel.SetActive(false);
        sendButton.onClick.AddListener(SendQuestion);
        closeButton.onClick.AddListener(CloseInterface);
    }
    
    private void Update()
    {
        if (Keyboard.current != null && Keyboard.current.hKey.wasPressedThisFrame)
        {
            bool newState = !AgentUIController.ShowBubbles;
            
            AgentUIController[] allUIs = FindObjectsOfType<AgentUIController>();
            foreach (var ui in allUIs)
            {
                ui.ToggleBubbles(newState);
            }
        }
    }

    public void OpenInterface(string agentId)
    {
        currentAgentId = agentId;
        headerText.text = "Conversation with " + agentId;
        answerText.text = "Type your question...";
        inputField.text = "";
        qaPanel.SetActive(true);
        IsPanelActive = true;
    }

    public void CloseInterface()
    {
        qaPanel.SetActive(false);
        currentAgentId = string.Empty;
        IsPanelActive = false;
    }

    private void SendQuestion()
    {
        if (string.IsNullOrEmpty(inputField.text) || string.IsNullOrEmpty(currentAgentId)) return;

        UnityEventRequest<UserQuestionData> request = new UnityEventRequest<UserQuestionData>
        {
            type = "user_question",
            agent_id = "system",
            timestamp = DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1)).TotalSeconds,
            data = new UserQuestionData
            {
                targetAgentId = currentAgentId,
                question = inputField.text
            }
        };

        string json = JsonUtility.ToJson(request);
        WebSocketClientManager.Instance.SendMessageToServer(json);

        answerText.text = "Awaiting response...";
        inputField.text = "";
    }

    public void ReceiveAnswer(string agentId, string answer)
    {
        if (qaPanel.activeSelf && currentAgentId == agentId)
        {
            answerText.text = answer;
        }
    }
}