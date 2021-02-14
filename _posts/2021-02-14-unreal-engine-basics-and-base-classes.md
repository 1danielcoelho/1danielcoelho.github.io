---
layout: post
title: Unreal Engine basics and base classes
tags: unreal
---

This is going to be the first of a few of blog posts detailing some stuff I've learned doing deep dives in the Unreal Engine source.

This is mostly to get the ball rolling as far as this blog is concerned (as working with Unreal is a large part of my day job and should be the easiest to write about), but also because UE's documentation is not the best, and there's a surprising shortage of posts like this out there. It seems like the community just assumes everyone is forced to dig through the code, and while there's nothing fundamentally wrong with reading code, it does get in the way a bit when all you want is an overview. It also sucks that everyone has to rediscover the same insights over and over, so hopefully this can provide a net saving of man hours to the world.

This post is about UE 4.26 in particular, but most of these details probably haven't changed much since UE 3.

I will sometimes link straight to the UE source on Github at some points. If you don't have access to it yet, you can get it for free in just a couple of seconds by following [this guide](https://www.unrealengine.com/en-US/ue4-on-github).

### UObjects

Let's get into it then! The purpose of this post is to explain how `UObject`, `UClass`, `UBlueprint`, `UBlueprintGeneratedClass` and other concepts like the Class Default Object all interact. Hopefully this post works as sort of a crash course on the base classes of the engine.

Let's start off with a simple, pure C++ class. I'm using a `TArray` data member here, but that's just an analogue for `std::vector`, so there's nothing special there.

```cpp
class MyObject
{
public:
    float Multiply(float OtherValue)
    {
        return MyValue * OtherValue;
    }

    float MyValue = 2.3f;
    TArray<double> MyValueArray;
    float UnAnnotatedValue = 3.0f;
};
```

In order to see `MyValue` and `MyValueArray` in the editor, interact with our class via blueprints or even create a blueprint class that derives `MyObject`, we need some changes:

```cpp
#include "UObject/ObjectMacros.h"
#include "MyObject.generated.h"

UCLASS( BlueprintType )
class UMyObject : public UObject
{
    GENERATED_BODY()

public:
    float Multiply(float OtherValue)
    {
        return MyValue * OtherValue;
    }

    float MyValue = 2.3f;
    TArray<int32> MyValueArray;
    float UnAnnotatedValue = 3.0f;
};
```

A few things happened here: We derived from `UObject`, which is the base class for objects managed by Unreal and is required to get our class garbage collected, replicated over the network, serialized, and more. We also had to rename our class to `UMyObject`, as that is the naming convention for classes that derive from `UObject`. We also added a couple of includes, and a couple of macros, which are required to get Unreal Header Tool (UHT) to automatically generate some code for us when we compile.

Note that these macros just expand to more macros, and won't help us understand what's going on (although you can peek at them [here](https://github.com/EpicGames/UnrealEngine/blob/5df54b7ef1714f28fb5da319c3e83d96f0bedf08/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h#L638) if you want). Instead, these macros work more as annotations: UHT will parse this code, see those anotations (like `UCLASS()`), and know that it needs to generate some code about that class and place it somewhere (and obviously remove the annotations afterwards).

Part of that generated code goes in that `"MyObject.generated.h"` file, and part of that code is injected in the location of that `GENERATED_BODY()` macro just before we compile. You will likely never need to interact with the `"*.generated.h"` files though, and that's good, because there's some pretty crazy auto-generated code in there.

You can provide some optional arguments to some of these annotations, like how we did `UCLASS( BlueprintType )`. That one in particular allows our `UMyObject` objects to interact with blueprints, but you can check out all the optional arguments you can provide on the actual source [here](https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h#L653).

If you're interested about this part, you can find some more details about reflection on [this](https://www.unrealengine.com/en-US/blog/unreal-property-system-reflection) excellent post by Michael Noland, and on [the official doc page](https://docs.unrealengine.com/en-US/ProgrammingAndScripting/ProgrammingWithCPP/UnrealArchitecture/Objects/index.html) for the unreal `UObject`s.

### UClasses

An important aspect of annotating our class for UHT like this is that it leads to a `UClass` object being generated for our `UMyObject` during engine initialization (both in the editor and for a packaged game). We also get a static function `UMyObject::StaticClass()` automatically generated and injected into our class definition, so we can do this to get a `UClass` object:

```cpp
UClass* MyObjectsClass = UMyObject::StaticClass();
```

> Warning: Don't get confused here! These `UClass` objects **themselves** derive from `UObject`, and so are garbage collected, reflected, and managed just like instances of our `UMyObject`. This is how you can still manipulate classes directly in the engine, like providing classes to blueprint nodes and creating properties of "Class" type (we will do this later!).

Getting back on track, that `UClass` instance we got there holds tons of useful data about our `UMyObject` type, like whatever data members and functions our class has that the engine can reason about.

> By the way, yes, there **is** a `UClass` for `UClass` objects as well! Rest assured you will rarely ever need to consider this, so you may ignore all of that for now and just consider `UClass` as a base class.

If we checked that `UClass* MyObjectsClass` object now we wouldn't find information about our data members and functions though. We need some more of those annotation macros for that:

```cpp
#include "UObject/ObjectMacros.h"
#include "MyObject.generated.h"

UCLASS()
class UMyObject : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION( BlueprintCallable )
    float Multiply(float OtherValue)
    {
        return MyValue * OtherValue;
    }

    UPROPERTY( EditAnywhere )
    float MyValue = 2.3f;

    UPROPERTY( EditAnywhere )
    TArray<int32> MyValueArray;

    float UnAnnotatedValue = 3.0f;
};
```

I've added the `UFUNCTION` and `UPROPERTY()` annotations with some useful self-explanatory optional arguments this time. You can find all of the optional arguments for `UFUNCTION` enumerated [here](https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h#L795) and for `UPROPERTY` enumerated [here](https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h#L887).

Now that our members are annotated, we could iterate our `UClass`'s fields and actually get info on our data members, like this:

```cpp
UClass* MyObjectsClass = UMyObject::StaticClass();

for ( TFieldIterator<FProperty> PropertyIterator( MyObjectsClass ); 
      PropertyIterator; 
      ++PropertyIterator )
{
    FProperty* Property = *PropertyIterator;
    
    // Would log "MyValue" and "MyValueArray"
    UE_LOG( LogTemp, Log, TEXT( "%s" ), *Property->GetName() ); 
}

for ( TFieldIterator<UFunction> FunctionIterator( MyObjectsClass ); 
      FunctionIterator; 
      ++FunctionIterator )
{
    UFunction* Func = *FunctionIterator;
    
    // Would log Multiply
    UE_LOG( LogTemp, Log, TEXT( "%s" ), *FunctionIterator->GetName() ); 
}
```

We can of course get tons of more useful information about those properties and functions, including their value size, metadata. This is the actual "reflection" capability I mentioned previously: Objects of `UMyObject` can query what data members and functions they own, and read/write to them. 

### Class default objects

One very important member of the `UClass` instance we got there is the Class Default Object (CDO). This object is just another instance of our `UMyObject` class, but it is owned by the `UClass` directly. It will hold the default values for our properties, and in some contexts it is used as a template for all other created instances. These CDOs are used everywhere throughout the engine, and have some surprising uses. 

For example, configuration and "options" container objects in Unreal are usually just `UObject`s too, and the properties are the actual options that you can set. When you edit them on the editor, what you're doing is editing the CDO object's values for those properties, and those values can be saved to disk and read back again later.

Take for example the `UBlueprintEditorSettings` class. It contains the options you see under "Blueprint Editor" on the Edit -> Editor Preferences window.

![Blueprint editor options](/assets/images/unreal-engine-basics-and-base-classes/blueprint-editor.png)

That class is defined at `Engine\Source\BlueprintGraph\Public\BlueprintEditorSettings.h` and [as of 4.26](https://github.com/EpicGames/UnrealEngine/blob/5df54b7ef1714f28fb5da319c3e83d96f0bedf08/Engine/Source/Editor/BlueprintGraph/Public/BlueprintEditorSettings.h#L21) looks like this:

```cpp
UCLASS(config=EditorPerProjectUserSettings)
class BLUEPRINTGRAPH_API UBlueprintEditorSettings
	:	public UObject
{
	  GENERATED_UCLASS_BODY()

// Style Settings
public:
    /** Should arrows indicating data/execution flow be drawn halfway along wires? */
    UPROPERTY(EditAnywhere, config, Category=VisualStyle, meta=(DisplayName="Draw midpoint arrows in Blueprints"))
    bool bDrawMidpointArrowsInBlueprints;

    /** Determines if lightweight tutorial text shows up at the top of empty blueprint graphs */
    UPROPERTY(EditAnywhere, config, Category = VisualStyle)
    bool bShowGraphInstructionText;

    /** If true, fade nodes which are not connected to the selected nodes */
    UPROPERTY(EditAnywhere, config, Category = VisualStyle)
    bool bHideUnrelatedNodes;

    /** If true, use short tooltips whenever possible */
    UPROPERTY(EditAnywhere, config, Category = VisualStyle)
    bool bShowShortTooltips;

    // A lot more stuff below
```

There is some code somewhere that automatically prettifies the variable names before showing it in the editor, so something like `bHideUnrelatedNodes` becomes `Hide Unrelated Nodes` automatically. You can override that and get it to show something else when viewed in the Editor by using the `UPROPERTY` argument `meta=(DisplayName="Something else")` though.

The cool thing is that at any point in your C++ code, if you wanted to get or set the value of `bHideUnrelatedNodes` for whatever reason, you can just do this:

```cpp
UBlueprintEditorSettings* Settings = GetMutableDefault<UBlueprintEditorSettings>();
Settings->bHideUnrelatedNodes = false;
Settings->SaveConfig();
```

> `GetMutableDefault<T>()` is just a convenience around `T::StaticClass()->GetDefaultObject()` by the way.

Another interesting bit is that `UCLASS(config=EditorPerProjectUserSettings)` annotation on top of `UBlueprintEditorSettings`. That means that the engine will serialize the CDO of that class to `<ProjectName>\Saved\Config\<Platform>\EditorPerProjectUserSettings.ini` whenever you call that `SaveConfig()` (which is a function defined directly on `UObject` by the way). This is what the corresponding part of that ini file looks like:

```ini
...

[/Script/BlueprintGraph.BlueprintEditorSettings]
bDrawMidpointArrowsInBlueprints=False
bShowGraphInstructionText=True
bHideUnrelatedNodes=False
bShowShortTooltips=True

...
```

### Debugging CDOs

Let's have a look at those CDOs and `UClass` objects in practice. In order to make it easy for us to analyze our objects, I'll make a quick actor that I can place on the level and interact with. It doesn't matter much for this post, but if you want to follow along it looks like this:

```cpp
#include "UObject/ObjectMacros.h"
#include "GameFramework/Actor.h"

#include "MyActor.generated.h"

UCLASS( Blueprintable )
class AMyActor : public AActor
{
	GENERATED_BODY()

public:
    UFUNCTION( BlueprintCallable )
    void ReceiveMyObject( UMyObject* Object );
};
```

Here is what the implementation of that one function looks like:

```cpp
#include "MyActor.h"

void AMyActor::ReceiveMyObject( UMyObject* Object )
{
    UClass* StaticClass = UMyObject::StaticClass();
    UClass* Class = Object->GetClass();

    UMyObject* CDO = Class->GetDefaultObject<UMyObject>();

    // Get all the instances that use this CDO
    TArray<UObject*> InstancesOfCDO;
    CDO->GetArchetypeInstances(InstancesOfCDO);
}
```

I've placed a breakpoint at the end of `ReceiveMyObject`, so we can have a look at what happens when we give this function an instance of `UMyObject`:

![UMyObject instance received](/assets/images/unreal-engine-basics-and-base-classes/my-object-cdo-ann.png)

First of all, as a sanity check we can confirm (underlined in red) that `Object->GetClass() == UMyObject::StaticClass()`. That is also the same thing we get if we drill down to the `ClassPrivate` field of Object. We can also see that we can use `GetArchetypeInstances` to find all objects that have `CDO` as a default in any way, and it found the same object that we received (underlined in green). "Archetype" here just roughly means that the object can be used as a template. There's more nuance to that, but we'll explore this in more detail in a future post.

Also note that the CDO for the `UMyObject` class has the values that it got from our C++ default member initializers (e.g. when we wrote `float MyValue = 2.3f;` directly on the class declaration). You could use the regular C++ constructor to initialize those values if you want, though. The point is that the CDO is just another regular instance of that class.

By the way, on the visual scripting side, you can use the `GetClassDefaults` blueprint node to read (but not set) the property values on the CDO.

If you doubted me before about the `UClass` holding the reflected data about members, have a look at this:

![UMyObject UClass on debug](/assets/images/unreal-engine-basics-and-base-classes/debug-static-class-ann.png)

I've expanded `UMyObject`'s `UClass`. We can clearly in red where it holds information about our `Multiply` `UFunction`, as well as our `MyValue` float property and our `MyValueArray` array property. It stores it in a linked list, and there's no sign of our `UnAnnotatedValue`, since it wasn't annotated. It would have been pointed to by the `Next` pointer in green if it were annotated though.

One last important thing you should know about CDOs: It's very likely that they will be constructed during engine initialization along with their owner `UClass` objects, where a lot of other things aren't fully initialized. The CDO is otherwise just a regular instance of our `UMyObject` though, and it will call the regular C++ constructor when being created, if you have one defined. This means that whatever we put in our constructors for `UObject`-derived classes like our `UMyObject` shouldn't really expect much from its context or try using other classes too much, as they may not have been initialized yet. 

If it's unavoidable, you can usually check if that particular instance of `UMyObject` is a CDO or not by calling `UObject::IsTemplate()`, and not doing your context-dependent initialization in that case. Something like this:

```cpp
UMyObject::UMyObject()
{
    if( !IsTemplate() )
    {
        // Do things that may not work during engine initialization
    }
}
```

### UBlueprints

Objects of our `UMyObject` class can be manipulated by the engine now: Instances of those would be replicated, serialized and garbage collected like you'd expect, and can interact with the many different subsystems in Unreal, like Niagara and the Sequencer and whatever. This could be all you need, especially if whatever you're building is more on the C++ side.

If you're building something more on the visual scripting side, then you'll likely want to create blueprint functions on your `UMyObject`, and have it interact with your level and other blueprints that way. We can accomplish that by creating a blueprint class that derives from the `UMyObject` class, by first clicking `Add/Import`, picking `Blueprint Class`...

![Creating a blueprint](/assets/images/unreal-engine-basics-and-base-classes/create-blueprint.png)

... and then choosing our `UMyObject` object as a base class (note that the `U` prefix is dropped here, as well as through most of the Editor). 

![Deriving UMyObject](/assets/images/unreal-engine-basics-and-base-classes/deriving-myobject.png)

I'll name our derived blueprint class "`DerivedObject`", so we now get a new asset on our content browser that looks like this:

![DerivedObject asset](/assets/images/unreal-engine-basics-and-base-classes/derived-object.png)

This asset is a `UBlueprint` asset, also known as a `Blueprint Class`. This is not a `UClass`, nor a CDO, nor an instance of `DerivedObject`, it is something entirely different. If you double-click this it will open a Blueprint Editor, that looks like this:

![DerivedObject editor](/assets/images/unreal-engine-basics-and-base-classes/derived-object-editor-ann.png)

The red arrow points to the base class: In our case it corresponds to our `UMyObject` class. If you click on the `Class Defaults` button pointed to in orange, the area on the right (pointed to in green) will display some property values.

What you're looking at on the right are the values of `DerivedObject`'s CDO's properties, which on the blueprint/visual scripting side are usually referred to as "Class Defaults". In particular, you can see a `UMyObject` section for the properties that the `DerivedObject` class gets by deriving `UMyObject`, i.e. `My Value` and `My Value Array` (it prettified our property names here too, like it did for `UBlueprintEditorSettings`). If we create a new variable on our `DerivedObject` class (which we will do later), the CDO's value for it would show up here, in another section.

Note how we never set these values before: They are initially set with whatever the defaults are on the base class (i.e. `UMyObject` for us). Defaults are specific to each class though, so we could set this to `5.0f`, and that value would be used for `DerivedObject` instances, while `2.3f` would still be used for `UMyObject` instances.

Another useful thing to know is that if you have a few instances of `DerivedObject` out there with `MyValue == 2.3f`, and using this editor you change the default from `2.3f` to `2.5f`, all of those instances would be updated too. Their properties would not be updated if their values differed from the CDO's by the time the CDO's changed, though, so you get to keep your manually set values if you have them.

Let's have a look at what happens when we provide a `DerivedObject` to our `ReceiveMyObject` function from before. Remember, `UMyObject` is a parent class of `DerivedObject`, and because our parameter is just a pointer to the base class, we can receive a `DerivedObject` with no changes to our function.

![DerivedObject's CDO](/assets/images/unreal-engine-basics-and-base-classes/derived-object-cdo.png)

Check it out, `Object`'s class, and it's CDO class are no longer the same as `UMyObject::StaticClass()`, they're something else now. If you look at the type (far right on the lines underlined in green) you'll see that they're `UBlueprintGeneratedClass`, being pointed to via a `UClass*`. The rest is working as expected though: It can find the same object we received when we check `InstancesOfCDO`.

The `UBlueprintGeneratedClass` type derives from `UClass`, and describes a `UClass` that was generated based on a `UBlueprint`. When you open the Blueprint Editor like before and add a function or a variable, a new `UBlueprintGeneratedClass` will be generated, containing the compiled info from your blueprint. Let's expand that `UBlueprintGeneratedClass` we got:

![BlueprintGeneratedClass](/assets/images/unreal-engine-basics-and-base-classes/blueprint-gen-class.png)

At the very top, still underlined in green, you can see that the same `UClass` object at address `0x0000021d0d70dd00` we were looking at in the previous image. Check it out though, if you drill down to its `UStruct` base class, you can see underlined in red how it is pointing at `UMyObject::StaticClass()` as a `SuperStruct` (i.e. parent class). The exact same `UClass` is also underlined in red on the previous image.

If you peek a few lines below `SuperStruct`, you can see the `Children` and `ChildProperties` members pointing at the fields of `UMyObject`. Our `DerivedObject` doesn't have any extra variables or functions, but if it did you would find them on the `ChildProperties` member owned directly by the `UBlueprintGeneratedClass`, underlined in light blue.

Finally, you can see two extra things: The `ClassGeneratedBy` field of this `UBlueprintGeneratedClass` points at our `UBlueprint` asset we saw at the content browser. Also, we can see at the very bottom of this image how the `UBlueprintGeneratedClass` is pointing at the CDO of `DerivedObject` that we retrieved on the previous image.

Lets try modifying our `DerivedObject` a little bit. I'll add an extra empty function, a variable, and change the CDO value for `MyValue`. You can also see the CDO's value for the `NewVariable` on the right pane:

![BlueprintGeneratedClass](/assets/images/unreal-engine-basics-and-base-classes/edited-derived-object-bp.png)

If we compile this, then provide a new `DerivedObject` to `ReceiveMyObject` and peek at its `UBlueprintGeneratedClass` again, this is what we get:

![BlueprintGeneratedClass](/assets/images/unreal-engine-basics-and-base-classes/edited-derived-object-bp-debug.png)

Underlined in blue you can see how `Children` now points to the new `TestFunction`, and how `ChildProperties` now points to our `NewVariable`. These were `nullptr` before. Also, Visual Studio is telling us something here: Note how our CDO at the very bottom is written in red text: This means the field has changed, and it is now pointing at a new object entirely. 

This is because every time you compile your `UBlueprint`, the engine will replace all instances of your `UBlueprintGeneratedClass` with brand new ones (copying over any custom property values you could have), and that includes the CDO. If you want to have a look at this part of the source, I recommend starting out [at this file](https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Editor/UnrealEd/Public/Kismet2/KismetReinstanceUtilities.h).

You should know that a lot of the blueprint-related stuff is editor-only, and is not available at the cooked game. Essentially, when you compile your blueprints they all become `UFUNCTION`s and `UPROPERTY`s, and mostly that's all you need.

There's still a couple of things I want to show you though, because they can be quite confusing at times. Check out this code:

```cpp
UClass* BaseClass = UMyObject::StaticClass();
UMyObject* BaseCDO = BaseClass->GetDefaultObject<UMyObject>();

UMyObject* BaseBefore = NewObject<UMyObject>( this, BaseClass, NAME_None, RF_NoFlags, BaseCDO );
UE_LOG( LogTemp, Log, TEXT( "BaseBefore: %f" ), BaseBefore->MyValue );

// This value starts out at 2.3f, but we'll change it to 3.0f
BaseCDO->MyValue = 3.0f;

UMyObject* BaseAfter = NewObject<UMyObject>( this, BaseClass, NAME_None, RF_NoFlags, BaseCDO );
UE_LOG( LogTemp, Log, TEXT( "BaseBefore: %f, BaseAfter: %f" ), BaseBefore->MyValue, BaseAfter->MyValue );
```

And the analogue for `DerivedObject`:

```cpp
UClass* DerivedClass = LoadClass<UMyObject>( NULL, TEXT( "Blueprint'/Game/DerivedObject.DerivedObject_C'" ) );
UMyObject* DerivedCDO = DerivedClass->GetDefaultObject<UMyObject>();

UMyObject* DerivedBefore = NewObject<UMyObject>( this, DerivedClass, NAME_None, RF_NoFlags, DerivedCDO );
UE_LOG( LogTemp, Log, TEXT( "DerivedBefore: %f" ), DerivedBefore->MyValue );

// This value starts out at 5.0f, but we'll change it to 6.0f
DerivedCDO->MyValue = 6.0f;

UMyObject* DerivedAfter = NewObject<UMyObject>( this, DerivedClass, NAME_None, RF_NoFlags, DerivedCDO );
UE_LOG( LogTemp, Log, TEXT( "DerivedBefore: %f, DerivedAfter: %f" ), DerivedBefore->MyValue, DerivedAfter->MyValue );
```

A couple of things are worth mentioning before we analyze the output:

- You can load your blueprint class using that `LoadClass` call, but also don't miss the fact that we're providing the path "Blueprint'/Game/DerivedObject.DerivedObject**\_C**'". The \_C suffix forms the path we need to retrieve the `UBlueprintGeneratedClass` stored inside the `UBlueprint` asset;
- To create our `DerivedObject` instances we're calling `NewObject<UMyObject>` instead. We can't just do `NewObject<DerivedObject>` as `DerivedObject` is not a C++ type, it's just a blueprint class. This is perfectly fine though: We're providing `DerivedClass` to `NewObject` anyway. It will create an instance of the derived class (a `DerivedObject`), and return a polymorphic pointer to it.

Anyway, when we run his code, we get this output:

```log
LogTemp: BaseBefore: 2.300000
LogTemp: BaseBefore: 2.300000, BaseAfter: 2.300000
LogTemp: DerivedBefore: 5.000000
LogTemp: DerivedBefore: 5.000000, DerivedAfter: 6.000000
```

Notice how updating the value in the CDO had no effect on new `UMyObject` instances, while it affected new `DerivedObject` instances. As it turns out, in the general case only blueprint classes (i.e. types whose class is a `UBlueprintGeneratedClass`) automatically get the provided template's values upon construction (you can have a look at where this is checked for [over here](https://github.com/EpicGames/UnrealEngine/blob/5df54b7ef1714f28fb5da319c3e83d96f0bedf08/Engine/Source/Runtime/CoreUObject/Private/UObject/UObjectGlobals.cpp#L2971)). This can be confusing because the `NewObject` function has a doc comment that suggests it would always copy things over from the CDO, but apparently not.

Also notice how in neither case the objects constructed before we changed the CDO were automatically updated to the new values when we modified the CDO. This can also be a bit confusing because the "automatic update" behavior only happens if the change to the CDO is done via the Editor. As far as I can tell there's no easy way of doing this via C++, because the code is private to the `PropertyEditor` module, but if you need that functionality you can have a look at [how the Property Editor does it](https://github.com/EpicGames/UnrealEngine/blob/5df54b7ef1714f28fb5da319c3e83d96f0bedf08/Engine/Source/Editor/PropertyEditor/Private/PropertyHandleImpl.cpp#L456) and replicate it.

As a closing remark, note that I edited the CDO like this to prove a point, but be careful when doing that in your project: The engine only creates one CDO for each class, and that is used as template for instances spawned in the editor, as well any instances spawned when you're testing via Play In Editor. Additionally, the CDO's values for `UBlueprintGeneratedClass`es are saved directly to the `UBlueprint` asset. This means that if you go into Play In Editor, get your CDO modified, then exit Play in Editor and save the `UBlueprint` asset, those changes would persist forever, and this is likely not what you want.

### Conclusion

Congratulations for surviving this UE4 whirlwind tour!

This turned out a lot larger than I thought it would, sorry about that. Even so there are many more things to talk about, but hopefully this helps to get some traction with the base UE4 C++ classes. It is quite a lot of stuff to take in at once, that's for sure.

I have some next posts already planned, but leave a comment if there's anything in particular you want me to talk about or explore next, or if you find out any mistakes or badly explained sections. I'll likely refer to this post in the future, so it would be neat if it was kept in tip-top shape.

Thanks for reading!
