

# class Node:
#     def __init__(self,data) -> None:
#         self.data=data
#         self.next=None
    


# def create():
#     head=Node(None)
#     return head

# def create_list():
#     head=create()
#     p=head
    
#     for i in range(10):
#         node=Node(i)
#         p.next=node
#         p=p.next

#     p.next=None

#     return head

# def print_node(head:Node):

#     p=head
#     p=p.next

#     for i in range(10):
#         print(p.data)
#         p=p.next


# print_node(create_list())

        

class Node:
    def __init__(self,data):
        self.data=data
        self.item=None
#创建链表
def _create_node():
    head=Node(None)
    return head

head=_create_node()
tail=head
while True:
    value=input("请输入节点的值（输入q停止）：")
    if value=='q':
       tail.item=None
       break
    else:
        node=Node(value)
        tail.item=node
        tail=tail.item
       
 #输出链表
def print_linked_list(head):
    current = head.item

    while current:
        print(current.data)
        current = current.item

print_linked_list(head=head)

print("链表的值为：")