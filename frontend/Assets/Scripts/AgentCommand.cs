using UnityEngine;

public enum CommandType {Interact, Wait }

[System.Serializable]
public class AgentCommand
{
    public CommandType Type;
    public Vector3 Destination;
    public MonoBehaviour TargetInteractable;
    public float WaitTime;
}