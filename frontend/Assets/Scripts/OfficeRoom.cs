using UnityEngine;

public enum RoomType 
{ 
    Reception, Main, Boss, Working, Diner, File, Conference 
}

public class OfficeRoom : MonoBehaviour
{
    public RoomType roomType;
    public Transform doorNode;
    public BoxCollider roomCollider;
}