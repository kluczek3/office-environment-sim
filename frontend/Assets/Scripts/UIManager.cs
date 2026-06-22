using UnityEngine;
using UnityEngine.UI;

public class UIManager : MonoBehaviour
{
    public GameObject startPanel;
    public GameObject loadingPanel;

    private void Start()
    {
        startPanel.SetActive(true);
        loadingPanel.SetActive(false);
    }

    public void OnStartSimulationClicked()
    {
        startPanel.SetActive(false);
        loadingPanel.SetActive(true);
        
        _ = WebSocketClientManager.Instance.ConnectAsync();
    }

    public void HideLoadingScreen()
    {
        loadingPanel.SetActive(false);
    }
}