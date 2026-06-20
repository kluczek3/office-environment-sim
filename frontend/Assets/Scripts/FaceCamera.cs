using UnityEngine;

public class FaceCamera : MonoBehaviour
{
    private Camera mainCam;

    private void Start()
    {
        mainCam = Camera.main;
    }

    private void LateUpdate()
    {
        if (mainCam != null)
        {
            transform.LookAt(transform.position + mainCam.transform.rotation * Vector3.forward,
                mainCam.transform.rotation * Vector3.up);
        }
    }
}