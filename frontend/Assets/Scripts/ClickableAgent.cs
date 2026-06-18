using UnityEngine;
using UnityEngine.InputSystem; 

[RequireComponent(typeof(Collider))]
public class ClickableAgent : MonoBehaviour
{
    private SimulationEntity entity;

    private void Awake()
    {
        entity = GetComponentInParent<SimulationEntity>();
    }

    private void Update()
    {
        if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame)
        {
            Ray ray = Camera.main.ScreenPointToRay(Mouse.current.position.ReadValue());
            RaycastHit[] hits = Physics.RaycastAll(ray);

            foreach (RaycastHit hit in hits)
            {
                ClickableAgent clickedAgent = hit.collider.GetComponentInParent<ClickableAgent>();
                
                if (clickedAgent == this)
                {
                    if (entity != null)
                    {
                        if (QAInterfaceManager.Instance != null)
                        {
                            QAInterfaceManager.Instance.OpenInterface(entity.UniqueIdentifier);
                        }
                    }
                }
            }
        }
    }
}