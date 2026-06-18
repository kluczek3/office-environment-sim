using UnityEngine;
using UnityEngine.InputSystem;

public class FreeFly : MonoBehaviour 
{
    public float speed = 10f;
    public float sensitivity = 0.2f;

    void Update() 
    {
        if (QAInterfaceManager.Instance != null && QAInterfaceManager.Instance.IsPanelActive)
        {
            return;
        }

        var mouse = Mouse.current;
        if (mouse != null && mouse.rightButton.isPressed) 
        { 
            Vector2 delta = mouse.delta.ReadValue();
            float rotX = transform.localEulerAngles.y + delta.x * sensitivity;
            float rotY = transform.localEulerAngles.x - delta.y * sensitivity;
            transform.localEulerAngles = new Vector3(rotY, rotX, 0);
        }
        
        var kb = Keyboard.current;
        if (kb != null) 
        {
            Vector3 move = Vector3.zero;
            if (kb.wKey.isPressed) move += transform.forward;
            if (kb.sKey.isPressed) move -= transform.forward;
            if (kb.aKey.isPressed) move -= transform.right;
            if (kb.dKey.isPressed) move += transform.right;

            transform.position += move * (speed * Time.deltaTime);
        }
    }
}