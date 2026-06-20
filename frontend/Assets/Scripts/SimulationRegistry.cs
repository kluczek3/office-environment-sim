using System.Collections.Generic;
using UnityEngine;

public static class SimulationRegistry
{
    private static readonly Dictionary<string, SimulationEntity> Entities = new Dictionary<string, SimulationEntity>();
    private static readonly Dictionary<string, int> TypeCounters = new Dictionary<string, int>();

    public static void Register(SimulationEntity entity)
    {
        if (string.IsNullOrEmpty(entity.UniqueIdentifier))
        {
            string typeKey = string.IsNullOrEmpty(entity.BaseType) ? "object" : entity.BaseType;
            if (!TypeCounters.ContainsKey(typeKey))
            {
                TypeCounters[typeKey] = 0;
            }
            entity.SetGeneratedId(typeKey + "_" + TypeCounters[typeKey]++);
        }

        if (!Entities.ContainsKey(entity.UniqueIdentifier))
        {
            Entities.Add(entity.UniqueIdentifier, entity);
        }
    }

    public static void Unregister(SimulationEntity entity)
    {
        if (entity != null && Entities.ContainsKey(entity.UniqueIdentifier))
        {
            Entities.Remove(entity.UniqueIdentifier);
        }
    }

    public static SimulationEntity GetEntity(string id)
    {
        if (Entities.TryGetValue(id, out SimulationEntity entity))
        {
            return entity;
        }
        return null;
    }

    public static List<SimulationEntity> GetEntitiesByBaseType(string baseType)
    {
        List<SimulationEntity> result = new List<SimulationEntity>();
        foreach (var entity in Entities.Values)
        {
            if (entity.BaseType == baseType)
            {
                result.Add(entity);
            }
        }
        return result;
    }
}