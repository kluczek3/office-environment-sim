using UnityEngine;

public class SimulationEntity : MonoBehaviour
{
    [SerializeField] private string baseType;
    [SerializeField] private string manualIdentifier;
    private string uniqueIdentifier;

    public string UniqueIdentifier => uniqueIdentifier;
    public string BaseType => baseType;

    private void Awake()
    {
        if (!string.IsNullOrEmpty(manualIdentifier))
        {
            uniqueIdentifier = manualIdentifier;
        }
        SimulationRegistry.Register(this);
    }

    public void OverrideIdentifier(string newId)
    {
        SimulationRegistry.Unregister(this);
        uniqueIdentifier = newId;
        SimulationRegistry.Register(this);
    }

    public void SetGeneratedId(string generatedId)
    {
        if (string.IsNullOrEmpty(uniqueIdentifier))
        {
            uniqueIdentifier = generatedId;
        }
    }

    private void OnDestroy()
    {
        SimulationRegistry.Unregister(this);
    }
}