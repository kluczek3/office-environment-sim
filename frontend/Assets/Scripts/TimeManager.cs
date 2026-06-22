using System;
using UnityEngine;

namespace Simulation.Network
{
    public class TimeManager : MonoBehaviour
    {
        public static TimeManager Instance { get; private set; }

        [SerializeField] private int startHour = 9;
        [SerializeField] private int startMinute = 0;
        [SerializeField] private float secondsPerInGameMinute = 1.0f;

        private float currentInGameMinutes;

        public float TimeScale => secondsPerInGameMinute;

        private void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
                DontDestroyOnLoad(gameObject);
            }
            else
            {
                Destroy(gameObject);
            }

            currentInGameMinutes = (startHour * 60) + startMinute;
        }

        private void Update()
        {
            currentInGameMinutes += (Time.deltaTime / secondsPerInGameMinute);
        }

        public string GetFormattedTime()
        {
            int hours = Mathf.FloorToInt(currentInGameMinutes / 60) % 24;
            int minutes = Mathf.FloorToInt(currentInGameMinutes % 60);
            return $"{hours:D2}:{minutes:D2}";
        }

        public void AdvanceTime(float minutesToAdd)
        {
            currentInGameMinutes += minutesToAdd;
        }
    }
}