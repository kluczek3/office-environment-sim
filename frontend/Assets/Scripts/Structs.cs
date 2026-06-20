using UnityEngine;
using System;
using System.Collections.Generic;

public struct TargetPose
{
    public Vector3 Position;
    public Quaternion Rotation;

    public TargetPose(Vector3 position, Quaternion rotation)
    {
        Position = position;
        Rotation = rotation;
    }
}

public enum AgentRole
{
    Worker,
    Boss,
    Receptionist
}

[Serializable]
public class BackendCommandBuffer
{
    public List<BackendCommand> commands;
}

[Serializable]
public class BackendCommand
{
    public string agentId;
    public string actionType;
    public string targetId;
    public bool isEmergency;
    public float duration;
}


