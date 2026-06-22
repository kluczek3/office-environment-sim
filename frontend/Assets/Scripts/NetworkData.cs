using System;
using System.Collections.Generic;
using UnityEngine;

namespace Simulation.Network
{
    [Serializable]
    public class UnityEventRequest<T>
    {
        public string type;
        public string agent_id;
        public double timestamp;
        public T data;
    }

    [Serializable]
    public class ActionRequestData
    {
        public string current_location;
        public string current_time;
    }

    [Serializable]
    public class InitializationData
    {
        public List<AgentInitInfo> agents;
        public List<string> zones;
    }

    [Serializable]
    public class AgentInitInfo
    {
        public string agentId;
        public string role;
        public string assignedChairId;
    }

    [Serializable]
    public class UserQuestionData
    {
        public string targetAgentId;
        public string question;
    }

    [Serializable]
    public class BackendResponse
    {
        public string type;
        public string agent_id;
        public string answer;
        public List<NetworkCommand> commands;
    }

    [Serializable]
    public class NetworkCommand
    {
        public string type;
        public string target_id;
        public float duration;
        public string thought;
    }
}