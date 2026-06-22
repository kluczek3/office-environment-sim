using System.Collections;
using UnityEngine;

[RequireComponent(typeof(BoxCollider))]
public class Door : MonoBehaviour
{
    public enum DoorType { StandardSwing, ReceptionUp }

    public DoorType doorType = DoorType.StandardSwing;
    public Transform doorMesh;
    public float openSpeed = 5f;
    public float closeDelay = 3f;

    private Quaternion closedRotation;
    private Quaternion openRotation;
    private Coroutine doorCoroutine;

    private void Awake()
    {
        closedRotation = doorMesh.localRotation;
        
        if (doorType == DoorType.StandardSwing)
        {
            openRotation = closedRotation * Quaternion.Euler(0, 90f, 0);
        }
        else if (doorType == DoorType.ReceptionUp)
        {
            openRotation = closedRotation * Quaternion.Euler(0, 0, 90f);
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.GetComponentInParent<AgentController>() != null)
        {
            if (doorCoroutine != null) StopCoroutine(doorCoroutine);
            doorCoroutine = StartCoroutine(OpenAndCloseRoutine());
        }
    }

    private IEnumerator OpenAndCloseRoutine()
    {
        yield return StartCoroutine(MoveDoor(openRotation));
        yield return new WaitForSeconds(closeDelay);
        yield return StartCoroutine(MoveDoor(closedRotation));
    }

    private IEnumerator MoveDoor(Quaternion targetRotation)
    {
        while (Quaternion.Angle(doorMesh.localRotation, targetRotation) > 0.1f)
        {
            doorMesh.localRotation = Quaternion.Lerp(doorMesh.localRotation, targetRotation, Time.deltaTime * openSpeed);
            yield return null;
        }
        doorMesh.localRotation = targetRotation;
    }
}