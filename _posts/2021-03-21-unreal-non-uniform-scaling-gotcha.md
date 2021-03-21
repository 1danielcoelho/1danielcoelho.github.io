---
layout: post
title: Gotcha when using FTransforms in Unreal Engine
tags: unreal
description: How to use non-uniform scaling FTransforms in Unreal Engine and avoid some problems
---

So this issue cost me about a day of my life. Hopefully you get to this post before the problem wastes your time too.

The `FTransform` struct in UE is a decomposed transform representation, which means it internally just contains an `FQuat` rotation, an `FVector` translation and a `FVector` scale. This is in contrast with `FMatrix`, which is just a regular 4x4 matrix that can be used as a transformation.

One major, sneaky problem with this is that you may run into trouble when using non-uniform scaling (i.e. the scale vector has different values for two or more components, like `[3.0, 1.0, 1.0]`).

First, let's have a look what happens when all you have is uniform scaling:

``` C++
FTransform A{ 
    FRotator{},                 // Rotation
    FVector{1.0f, 2.0f, 3.0f},  // Translation
    FVector{2.0f, 2.0f, 2.0f}   // Scale
};
FTransform AInv = A.Inverse();
FTransform AMaybeIdentity = A * AInv;

FVector Pos = FVector{ 50.0f, 60.0f, 70.0 };
FVector PosAfterA = A.TransformPosition( PosA );
FVector PosAfterAInv = AInv.TransformPosition( PosAfterA );
```

Print all this out and you get something like this:

```
A: 
    Trans:    [1.0, 2.0, 3.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0];  // Quaternions btw
    Scale:    [2.0, 2.0, 2.0]

AInv: 
    Trans:    [-1.0, -2.0, -3.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0]; 
    Scale:    [0.5, 0.5, 0.5]

AMaybeIdentity: 
    Trans:    [0.0, 0.0, 0.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0]; 
    Scale:    [1.0, 1.0, 1.0]

Pos:          [50.0, 60.0, 70.0]
PosAfterA:    [101.0, 122.0, 143.0]
PosAfterAInv: [50.0, 60.0, 70.0]
```

Nothing weird here. `AMaybeIdentity` is actually the identity, and transforming `Pos` with `A` and then `AInv` gets us back to `Pos`. Let's use non-uniform scaling instead:

``` C++
FTransform B{ 
    FRotator{},                   // Rotation
    FVector{ 1.0f, 2.0f, 3.0f },  // Translation
    FVector{ 2.0f, 1.0f, 1.0f }   // Scale
};
FTransform BInv = B.Inverse();
FTransform BMaybeIdentity = B * BInv;

FVector Pos = FVector{ 50.0f, 60.0f, 70.0 };
FVector PosAfterB = B.TransformPosition( PosB );
FVector PosAfterBInv = BInv.TransformPosition( PosAfterB );
```

Print the `B` case we get this:

```
B: 
    Trans:    [1.0, 2.0, 3.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0]; 
    Scale:    [2.0, 1.0, 1.0]

BInv: 
    Trans:    [-0.5, -2.0, -3.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0]; 
    Scale:    [0.5, 1.0, 1.0]

BMaybeIdentity: 
    Trans:    [0.0, 0.0, 0.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0]; 
    Scale:    [1.0, 1.0, 1.0]

Pos:          [50.0, 60.0, 70.0]
PosAfterB:    [101.0, 62.0, 73.0]
PosAfterBInv: [50.0, 60.0, 70.0]
```

...Oh? It still seems to work fine. I guess I don't need to pay attention to non-uniform scalings after all, right?

Let's just add a small rotation:

``` C++
FTransform C{ 
    FRotator{ 10.0f, 20.0f, 30.0f },    // Rotation
    FVector{ 1.0f, 2.0f, 3.0f },        // Translation
    FVector{ 2.0f, 1.0f, 1.0f }         // Scale
};
FTransform CInv = C.Inverse();
FTransform CMaybeIdentity = C * CInv;

FVector Pos = FVector{ 50.0f, 60.0f, 70.0 };
FVector PosAfterC = C.TransformPosition( PosC );
FVector PosAfterCInv = CInv.TransformPosition( PosAfterC );
```

This is what we get now:

```
C: 
    Trans:    [1.0, 2.0, 3.0]; 
    Rot:      [-0.239298329, -0.127679437, 0.144878119, 0.951548517]; 
    Scale:    [2.0, 1.0, 1.0]

CInv: 
    Trans:    [-1.65730095 -0.102469981 -3.23926759]; 
    Rot:      [0.239298329, 0.127679437, -0.144878119, 0.951548517]; 
    Scale:    [0.5, 1.0, 1.0]

CMaybeIdentity: 
    Trans:    [0.0, 0.0, 0.0]; 
    Rot:      [0.0, 0.0, 0.0, 1.0]; 
    Scale:    [1.0, 1.0, 1.0]

Pos:          [50.0, 60.0, 70.0]
PosAfterC:    [58.8023224, 115.580849, 50.5213852]
PosAfterCInv: [73.2543716, 66.2024841, 79.0265503] <--- !!!
```

Oh... oh no... 

Check how sneaky this is! `CMaybeIdentity` is still actually an identity. Only when you transform a point with `C` and then `CInv` that you see the problem: `PosAfterCInv != Pos`.

The actual problem happens when you apply the inverse. To understand what's going on, have a look at what `FTransform::TransformPosition` and `FTransform::Inverse` look like (roughly):

``` C++
FVector FTransform::TransformPosition(const FVector& V) const
{
	  return Rotation.RotateVector( Scale3D * V ) + Translation;
}

FTransform FTransform::Inverse() const
{
    FQuat   InvRotation = Rotation.Inverse();
    FVector InvScale3D = GetSafeScaleReciprocal( Scale3D );
    FVector InvTranslation = InvRotation * ( InvScale3D * -Translation );

    return FTransform( InvRotation, InvTranslation, InvScale3D );
}
```

The root of the problem is that `FTransform::TransformPosition` **always scales, then rotates, then translates, whether you're applying a transform or the inverse of a transform**. 

Ignore the translation for now: If you only have *uniform* scaling, then inverting the transform by applying the inverse scaling and then the inverse rotation is not a problem: It doesn't matter what rotation you applied to the object, since you'll scale it uniformly anyway.

The problem is that if you have non-uniform scaling, applying the inverse transform will first apply the inverse scale and only later inverse the rotation. This means the inverse scaling will happen around the rotated axes! 

To invert it properly using a decomposed representation you would need to do the steps in the reverse order: First apply the reverse translation, then apply the reverse rotation, and finally apply the reverse scale, which is not something that `FTransform::TransformPosition` will do. 

In UE you have 3 practical ways around this problem:

1. Apply the inverse translation, rotation and scaling manually in that order;

2. Use `FTransform::InverseTransformPosition`, which does exactly what we want:
``` C++
FVector FTransform::InverseTransformPosition(const FVector &V) const
{
	return (Rotation.UnrotateVector(V - Translation)) * GetSafeScaleReciprocal(Scale3D);
}
```
2. Or get the `FMatrix` from your transform, invert *that*, and transform your points with the inverted matrix instead:
``` C++
FMatrix CMatInv = C.ToMatrixWithScale().Inverse();
FVector CorrectPos = CMatInv.TransformPosition( PosAfterC ); // [50.0, 60.0, 70.0];
```

In conclusion, try to keep this annoyance in mind: This is the sort of thing that you learn about, forget it, and then get hit by it for critical damage later, like what happened to me. Maybe I'll remember this now that I've blogged about it.

TL;DR: Avoid using FTransform if you have non-uniform scalings and need the inverse transform, or pay **very** close attention to what you're doing!


Thanks for reading!