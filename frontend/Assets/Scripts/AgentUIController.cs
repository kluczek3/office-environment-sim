using UnityEngine;
using TMPro;

public class AgentUIController : MonoBehaviour
{
    public static bool ShowBubbles = true;

    [SerializeField] private GameObject bubbleContainer;
    [SerializeField] private TextMeshProUGUI thoughtText;

    private void Start()
    {
        bubbleContainer.SetActive(false);
    }

    public void ToggleBubbles(bool state)
    {
        ShowBubbles = state;
        if (!ShowBubbles)
        {
            bubbleContainer.SetActive(false);
        }
        else if (!string.IsNullOrEmpty(thoughtText.text))
        {
            bubbleContainer.SetActive(true);
        }
    }

    public void ShowThought(string text)
    {
        if (string.IsNullOrEmpty(text)) return;

        thoughtText.text = text;

        if (ShowBubbles)
        {
            bubbleContainer.SetActive(true);
        }
    }
}