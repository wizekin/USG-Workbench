"""Frame Library v0.1 (Foundation Package, spec Part 4 §4.12.2).

Layer 1/2 frames are GRAMMAR authority, layer 3 DOMAIN. ``kernel=True`` marks the
frames the first runnable kernel needs: the 20 frames of the specification plus
the four parametric specializations the kernel benchmark requires (OPEN, SEE,
ALLERGIC, OWNERSHIP_TRANSFER).

Refinement over the spec text (recorded as E-117): ATTITUDE declares only the
EXPERIENCER role. BELIEVE/KNOW (CONTENT is a proposition) and WANT (CONTENT is
an unasserted situation) each add their own CONTENT role, because a
specialization may not change a role's kind (SG-FRM-003).

Tier-1 parent choices exist for cross-frame alignment (e.g. OWNER maps to
RECIPIENT, the holder of what was received); they do not widen what a frame
accepts (E-45).
"""

from __future__ import annotations

from ..core.kinds import SemKind as K
from ..model.frames import (Authority, CompKind, ComponentSpec, Consequence, ConsequenceKind as CK, ControlHint,
                            ControlKind, FrameDef, FrameTests, LinkKind, ParamDecl, ParentLink, Perspective,
                            Presupposition, RoleDecl, SituationKind as SK, StatePattern as SP, Strength)

G, D = Authority.GRAMMAR, Authority.DOMAIN


def t1(name, req=False, kind=K.ENTITY, cls=None, card=1) -> RoleDecl:
    return RoleDecl(name, 1, None, kind, cls, req, card)


def t2(name, parent, req=False, kind=K.ENTITY, cls=None, card=1) -> RoleDecl:
    return RoleDecl(name, 2, parent, kind, cls, req, card)


def spec_of(parent: str, **maps) -> tuple[ParentLink, ...]:
    return (ParentLink(parent, LinkKind.SPECIALIZES, tuple(maps.items())),)


def T(valid, incomplete, invalid, contrastive) -> FrameTests:
    return FrameTests(tuple(valid), tuple(incomplete), tuple(invalid), tuple(contrastive))


EFF, TYP = Strength.ESSENTIAL, Strength.TYPICAL

FRAMES: tuple[FrameDef, ...] = (
    # ----------------------------------------------------------------- state change family
    FrameDef(
        "STATE_CHANGE", 1, G, SK.EVENT, kernel=True,
        roles=(t1("UNDERGOER", True), t1("AGENT", cls="Agent"), t1("CAUSE"),
               t2("INITIAL_STATE", "THEME", kind=K.STATE), t2("FINAL_STATE", "GOAL", kind=K.STATE),
               t1("TIME", kind=K.TIME)),
        params=(ParamDecl("DIMENSION", concept_kind=K.PROPERTY),
                ParamDecl("DIRECTION", ("TO_VALUE", "INCREASE", "DECREASE")),
                ParamDecl("TARGET_VALUE", concept_kind=K.VALUE)),
        final=(SP("HAS_VALUE", ("UNDERGOER", "param:TARGET_VALUE")),),
        process="CHANGE_OF_STATE",
        consequences=(Consequence(CK.EFFECT, EFF, SP("CHANGED", ("UNDERGOER", "param:DIMENSION"))),),
        tests=T(["The ice melted."], ["The ice melted. (no cause or agent stated)"],
                ["STATE_CHANGE with no UNDERGOER bound"], [("The ice melted.", "The ice did not melt.")]),
        doc="generic change of a property; children pin DIMENSION/DIRECTION/TARGET_VALUE"),
    FrameDef(
        "OPEN", 1, G, SK.EVENT, kernel=True, parents=spec_of("STATE_CHANGE"),
        pins=(("DIMENSION", "Openness"), ("DIRECTION", "INCREASE"), ("TARGET_VALUE", "OpenState")),
        roles=(t1("UNDERGOER", True, cls="Artifact"),),
        tests=T(["The door opened.", "John opened the door."], ["The door opened. (no agent: AGENT is UNSPECIFIED, never invented)"],
                ["OPEN with AGENT bound to a bare concept id"], [("John tried to open the door.", "John opened the door."),
                                                                  ("The door opened.", "The door did not open.")])),
    FrameDef(
        "CLOSE", 1, G, SK.EVENT, parents=spec_of("STATE_CHANGE"),
        pins=(("DIMENSION", "Openness"), ("DIRECTION", "DECREASE"), ("TARGET_VALUE", "ClosedState")),
        roles=(t1("UNDERGOER", True, cls="Artifact"),),
        tests=T(["The door closed."], ["The door closed. (agent unspecified)"], ["CLOSE with an unknown role"],
                [("The door closed.", "The door opened.")])),
    FrameDef(
        "FREEZE", 1, G, SK.EVENT, parents=spec_of("STATE_CHANGE"),
        pins=(("DIMENSION", "Phase"), ("DIRECTION", "TO_VALUE"), ("TARGET_VALUE", "PhaseSolid")),
        roles=(t1("UNDERGOER", True, cls="Substance"),),
        tests=T(["The water froze."], ["The water froze. (initial temperature never invented)"],
                ["FREEZE of an abstract entity"], [("The water froze.", "The water boiled.")])),
    FrameDef(
        "EXPERIENCE_STATE", 1, G, SK.STATE, kernel=True,
        roles=(t1("EXPERIENCER", True, cls="AnimateEntity"), t1("STIMULUS"), t2("DEGREE", "MEASURE", kind=K.VALUE),
               t1("TIME", kind=K.TIME)),
        params=(ParamDecl("STATE", concept_kind=K.STATE),),
        tests=T(["The patient is allergic to the medication."], ["The patient is allergic."], ["EXPERIENCE_STATE of a rock"],
                [("The patient is allergic to it.", "The patient is not allergic to it.")])),
    FrameDef(
        "ALLERGIC", 1, G, SK.STATE, kernel=True, parents=spec_of("EXPERIENCE_STATE"), pins=(("STATE", "Allergy"),),
        roles=(t1("STIMULUS", cls="Substance"),),
        tests=T(["The patient was allergic to it."], ["The patient was allergic."], ["ALLERGIC with STIMULUS an abstract idea"],
                [("The patient was allergic to the medication.", "The patient disliked the medication.")])),
    # ----------------------------------------------------------------- motion and location
    FrameDef(
        "MOVE", 1, G, SK.EVENT, kernel=True,
        roles=(t2("MOVER", "THEME", True, cls="PhysicalEntity"), t1("AGENT", cls="Agent"),
               t2("SOURCE_LOCATION", "SOURCE", cls="Location"), t2("DESTINATION_LOCATION", "GOAL", cls="Location"),
               t1("PATH"), t1("MANNER", kind=K.VALUE), t1("TIME", kind=K.TIME)),
        initial=(SP("LOCATED", ("MOVER", "SOURCE_LOCATION")),), final=(SP("LOCATED", ("MOVER", "DESTINATION_LOCATION")),),
        process="CHANGE_LOCATION",
        perspectives=(Perspective("ARRIVE", "DESTINATION_LOCATION", ("arrive", "reach")),
                      Perspective("DEPART", "SOURCE_LOCATION", ("leave", "depart"))),
        tests=T(["The car moved.", "John went to the hospital."], ["John left. (destination never invented)"],
                ["MOVE with a DESTINATION that is a person"], [("John arrived at the hospital.", "John left the hospital.")]),
        doc="entailments hold only for the completed view (aspect-gated, E-47)"),
    FrameDef(
        "LOCATED", 1, G, SK.STATE,
        roles=(t2("LOCATED_ENTITY", "THEME", True, cls="PhysicalEntity"), t1("LOCATION", True, cls="Location"),
               t1("TIME", kind=K.TIME)),
        tests=T(["The car is in the garage."], ["The car is located. (location unspecified)"], ["LOCATED of an abstract idea"],
                [("The car is in the garage.", "The car is near the garage.")])),
    # ----------------------------------------------------------------- transfer family
    FrameDef(
        "TRANSFER", 1, G, SK.EVENT, abstract=True, kernel=True,
        roles=(t1("AGENT", cls="Agent"), t1("SOURCE", True), t1("RECIPIENT", True, cls="Agent"), t1("THEME", True),
               t1("TIME", kind=K.TIME)),
        params=(ParamDecl("DIMENSION", ("CUSTODY", "POSSESSION", "OWNERSHIP")),),
        initial=(SP("HOLDS", ("SOURCE", "THEME", "param:DIMENSION")),),
        final=(SP("HOLDS", ("RECIPIENT", "THEME", "param:DIMENSION")),), process="CHANGE_HOLDER",
        tests=T(["(abstract) see GIVE"], ["(abstract) see GIVE"], ["instantiating TRANSFER directly"],
                [("John gave Mary a book.", "John offered Mary a book.")]),
        doc="abstract parent; physical, possession and ownership transfer are separate related frames"),
    FrameDef(
        "GIVE", 1, G, SK.EVENT, kernel=True, parents=spec_of("TRANSFER"), pins=(("DIMENSION", "POSSESSION"),),
        roles=(t1("AGENT", True, cls="Agent"),),
        perspectives=(Perspective("GIVE_VIEW", "AGENT", ("give", "hand")), Perspective("RECEIVE_VIEW", "RECIPIENT", ("receive", "get"))),
        consequences=(Consequence(CK.EFFECT, EFF, SP("HOLDS", ("RECIPIENT", "THEME", "param:DIMENSION"))),
                      Consequence(CK.TYPICAL_OUTCOME, TYP, SP("OWNS", ("RECIPIENT", "THEME")))),
        tests=T(["The doctor gave the patient medication.", "John gave Mary a book."],
                ["The patient was given medication. (AGENT and SOURCE UNSPECIFIED, nothing invented)"],
                ["GIVE with RECIPIENT bound to an abstract entity"],
                [("John gave Mary a book.", "John offered Mary a book."), ("John gave Mary a book.", "John lent Mary a book.")]),
        doc="the giver fills both AGENT and SOURCE (a referent may fill several roles)"),
    FrameDef(
        "RETURN", 1, G, SK.EVENT, kernel=True, parents=spec_of("TRANSFER"),
        params=(ParamDecl("RESTORES_PRIOR_HOLDER", ("TRUE",)),), pins=(("DIMENSION", "POSSESSION"), ("RESTORES_PRIOR_HOLDER", "TRUE")),
        tests=T(["He returned the book to Mary."], ["He returned it."], ["RETURN with no THEME bound"],
                [("He returned the book.", "He kept the book.")])),
    FrameDef(
        "OWNERSHIP_TRANSFER", 1, G, SK.EVENT, kernel=True, parents=spec_of("TRANSFER"), pins=(("DIMENSION", "OWNERSHIP"),),
        tests=T(["The company transferred the building to the city."], ["The building was transferred."],
                ["OWNERSHIP_TRANSFER with unknown role BUYER"], [("John sold Mary a car.", "John lent Mary a car.")])),
    FrameDef(
        "COMMERCIAL_TRANSACTION", 1, G, SK.EVENT, kernel=True,
        roles=(t2("BUYER", "AGENT", True, cls="Agent"), t2("SELLER", "AGENT", True, cls="Agent"),
               t2("GOODS", "THEME", True, cls="PhysicalEntity"), t2("MONEY", "THEME", cls="Money"), t1("TIME", kind=K.TIME)),
        disjoint_roles=(("BUYER", "SELLER"),),
        components=(ComponentSpec("OWNERSHIP_TRANSFER", (("GOODS", "THEME"), ("SELLER", "SOURCE"), ("BUYER", "RECIPIENT")), CompKind.DEPENDENCY),
                    ComponentSpec("OWNERSHIP_TRANSFER", (("MONEY", "THEME"), ("BUYER", "SOURCE"), ("SELLER", "RECIPIENT")), CompKind.DEPENDENCY)),
        perspectives=(Perspective("BUY", "BUYER", ("buy", "purchase")), Perspective("SELL", "SELLER", ("sell",)),
                      Perspective("PAY", "BUYER", ("pay",)), Perspective("COST", "GOODS", ("cost",))),
        tests=T(["John bought a car."], ["John bought a car. (seller and price never invented)"],
                ["COMMERCIAL_TRANSACTION where BUYER and SELLER are the same referent", "John bought the argument. (abstract GOODS is incompatible)"],
                [("John bought a car.", "John rented a car.")])),
    FrameDef(
        "OWN", 1, G, SK.STATE, kernel=True,
        roles=(t2("OWNER", "RECIPIENT", True, cls="Agent"), t2("OWNED_ENTITY", "THEME", True),
               t2("VALID_TIME", "TIME", kind=K.TIME)),
        tests=T(["John owns a car."], ["John owns it."], ["OWN with OWNER an abstract entity"], [("John owns a car.", "John rents a car.")])),
    FrameDef(
        "WORK", 1, G, SK.PROCESS, kernel=True,
        roles=(t2("WORKER", "AGENT", True, cls="Person"), t2("WORKPLACE", "LOCATION", cls="Location"),
               t2("EMPLOYER", "BENEFICIARY", cls="Organization"), t1("TIME", kind=K.TIME)),
        tests=T(["John works at the hospital."], ["John works."], ["WORK with WORKER a device"], [("John works at the hospital.", "John owns the hospital.")])),
    # ----------------------------------------------------------------- perception, communication, attitudes
    FrameDef(
        "PERCEIVE", 1, G, SK.EVENT, kernel=True,
        roles=(t1("EXPERIENCER", True, cls="AnimateEntity"), t1("STIMULUS", True), t1("INSTRUMENT", cls="Device"),
               t1("LOCATION", cls="Location"), t1("TIME", kind=K.TIME)),
        params=(ParamDecl("MODALITY", ("SIGHT", "HEARING", "TOUCH", "SMELL", "TASTE")),),
        tests=T(["John perceived the noise."], ["John perceived something."], ["PERCEIVE with EXPERIENCER a rock"],
                [("John saw the man.", "John heard the man.")])),
    FrameDef("SEE", 1, G, SK.EVENT, kernel=True, parents=spec_of("PERCEIVE"), pins=(("MODALITY", "SIGHT"),),
             tests=T(["John saw the man with a telescope."], ["John saw something."], ["SEE with MODALITY set by the instance"],
                     [("John saw the man.", "John watched the man.")])),
    FrameDef("HEAR", 1, G, SK.EVENT, parents=spec_of("PERCEIVE"), pins=(("MODALITY", "HEARING"),),
             tests=T(["John heard the noise."], ["John heard something."], ["HEAR with unknown role"], [("John heard it.", "John saw it.")])),
    FrameDef(
        "COMMUNICATE", 1, G, SK.EVENT, kernel=True,
        roles=(t2("SPEAKER", "AGENT", True, cls="Agent"), t2("ADDRESSEE", "RECIPIENT", cls="Agent"),
               t1("CONTENT", True, kind=K.PROPOSITION), t2("MEDIUM", "INSTRUMENT"), t1("TIME", kind=K.TIME)),
        tests=T(["John told Mary that it rained."], ["John said that it rained. (addressee unspecified)"],
                ["COMMUNICATE with CONTENT a bare concept id"], [("John said it rained.", "John knew it rained.")])),
    FrameDef(
        "ATTITUDE", 1, G, SK.STATE, abstract=True,
        roles=(t1("EXPERIENCER", True, cls="Agent"),),
        tests=T(["(abstract) see BELIEVE"], ["(abstract) see BELIEVE"], ["instantiating ATTITUDE directly"],
                [("John believes it.", "John knows it.")]),
        doc="abstract parent: CONTENT is declared by each child because its kind differs"),
    FrameDef(
        "BELIEVE", 1, G, SK.STATE, kernel=True, parents=spec_of("ATTITUDE"), roles=(t1("CONTENT", True, kind=K.PROPOSITION),),
        tests=T(["John believes that Mary left."], ["John believes it."], ["BELIEVE with CONTENT a person"],
                [("John believes it rained.", "John knows it rained.")])),
    FrameDef(
        "KNOW", 1, G, SK.STATE, kernel=True, parents=spec_of("ATTITUDE"), roles=(t1("CONTENT", True, kind=K.PROPOSITION),),
        presuppositions=(Presupposition("CONTENT"),),
        tests=T(["Mary knows that the meeting was cancelled."], ["Mary knows it."], ["KNOW with CONTENT a person"],
                [("Mary knows it rained.", "Mary believes it rained.")]),
        doc="factive: CONTENT is presupposed inside the same context (SG-EVD-004)"),
    FrameDef(
        "WANT", 1, G, SK.STATE, kernel=True, parents=spec_of("ATTITUDE"), roles=(t1("CONTENT", True, kind=K.EVENT),),
        control=ControlHint(ControlKind.SUBJECT_CONTROL, "EXPERIENCER", "CONTENT"),
        tests=T(["The boy wants to eat an apple."], ["The boy wants it."], ["WANT with CONTENT a bare concept id"],
                [("John wants to leave.", "John leaves.")]),
        doc="CONTENT is an unasserted situation; existence of its participants is scoped inside the wish"),
    FrameDef(
        "ATTEMPT", 1, G, SK.EVENT, kernel=True,
        roles=(t1("AGENT", True, cls="Agent"), t1("CONTENT", True, kind=K.EVENT), t2("OUTCOME", "GOAL", kind=K.VALUE)),
        control=ControlHint(ControlKind.SUBJECT_CONTROL, "AGENT", "CONTENT"),
        tests=T(["John tried to open the door."], ["John tried. (content unspecified)"], ["ATTEMPT with no CONTENT"],
                [("John tried to open the door.", "John opened the door.")]),
        doc="an attempt never entails its effect"),
    FrameDef(
        "OFFER", 1, G, SK.EVENT, kernel=True,
        roles=(t2("OFFERER", "AGENT", True, cls="Agent"), t2("OFFEREE", "RECIPIENT", cls="Agent"), t1("CONTENT", True, kind=K.EVENT)),
        tests=T(["John offered Mary a book."], ["John offered a book. (offeree unspecified)"], ["OFFER normalised to a completed GIVE"],
                [("John offered Mary a book.", "John gave Mary a book.")]),
        doc="an offer is never a completed transfer"),
    FrameDef(
        "CAUSATION", 1, G, SK.EVENT, kernel=True,
        roles=(t1("CAUSE", True, kind=K.PROPOSITION), t2("EFFECT", "GOAL", True, kind=K.PROPOSITION),
               t2("MECHANISM", "INSTRUMENT", kind=K.PROCESS), t2("CAUSE_TYPE", "MANNER", kind=K.VALUE)),
        tests=T(["The engine stopped because it overheated."], ["It stopped because of that. (mechanism unspecified)"],
                ["CAUSATION whose CAUSE is a bare concept id"], [("A caused B.", "A preceded B.")]),
        doc="relates PROPOSITIONS (E-118): a negated situation ('did not give') can be an effect, which a bare situation cannot. "
            "CAUSE_TYPE: DIRECT | ENABLING | PREVENTING | EXPLANATORY_REASON | PURPOSE"),
    # ----------------------------------------------------------------- medicine and eating
    FrameDef(
        "EXAMINATION", 1, G, SK.EVENT, kernel=True,
        roles=(t2("EXAMINER", "AGENT", True, cls="Person"), t2("EXAMINED_ENTITY", "THEME", True, cls="PhysicalEntity"),
               t1("INSTRUMENT", cls="Device"), t1("PURPOSE", kind=K.EVENT), t1("LOCATION", cls="Location"), t1("TIME", kind=K.TIME)),
        tests=T(["The doctor examined the patient.", "The patient was examined by the doctor."],
                ["The patient was examined. (EXAMINER is UNSPECIFIED, never invented)"],
                ["EXAMINATION binding the generic role AGENT instead of EXAMINER"],
                [("The doctor examined the patient.", "The patient examined the doctor.")])),
    FrameDef(
        "TREAT", 1, G, SK.EVENT, kernel=True,
        roles=(t2("PRACTITIONER", "AGENT", True, cls="Person"), t2("TREATED_ENTITY", "UNDERGOER", True, cls="AnimateEntity"),
               t2("CONDITION", "THEME", kind=K.STATE), t2("INTERVENTION", "INSTRUMENT"), t1("TIME", kind=K.TIME)),
        tests=T(["The doctor treated the patient."], ["The doctor treated the patient. (INTERVENTION unspecified)"],
                ["TREAT binding INSTRUMENT instead of INTERVENTION"], [("The patient was treated by the doctor.", "The patient treated the doctor.")])),
    FrameDef(
        "EAT", 1, G, SK.EVENT, kernel=True,
        roles=(t2("EATER", "AGENT", True, cls="AnimateEntity"), t2("FOOD", "UNDERGOER", True, cls="EdibleEntity"),
               t1("LOCATION", cls="Location"), t1("TIME", kind=K.TIME)),
        tests=T(["The boy eats an apple."], ["The boy ate. (food unspecified)"], ["EAT with EATER a pump", "EAT with FOOD an argument"],
                [("The boy ate the apple.", "The boy did not eat the apple.")])),
    # ----------------------------------------------------------------- functional / cross-domain (layers 2-3)
    FrameDef(
        "TRANSPORT", 2, G, SK.EVENT,
        roles=(t2("TRANSPORTED_ENTITY", "THEME", True, cls="PhysicalEntity"), t1("SOURCE"), t2("DESTINATION", "GOAL"),
               t2("MECHANISM", "INSTRUMENT"), t1("PATH"), t1("TIME", kind=K.TIME)),
        initial=(SP("LOCATED", ("TRANSPORTED_ENTITY", "SOURCE")),), final=(SP("LOCATED", ("TRANSPORTED_ENTITY", "DESTINATION")),),
        tests=T(["The conveyor transported the boxes."], ["The boxes were transported."], ["TRANSPORT of an abstract idea"],
                [("The pump moved the water.", "The pump stored the water.")]),
        doc="functional frame of FN.TRANSPORT"),
    FrameDef(
        "FLUID_TRANSPORT", 2, G, SK.EVENT, parents=spec_of("TRANSPORT"), roles=(t2("TRANSPORTED_ENTITY", "THEME", True, cls="Fluid"),),
        tests=T(["The pump moved water through the pipe."], ["The water was moved."], ["FLUID_TRANSPORT of a solid object"],
                [("The pump moved water.", "The pipe conducted water.")])),
    FrameDef(
        "BLOOD_CIRCULATION", 3, D, SK.EVENT, parents=spec_of("FLUID_TRANSPORT"), roles=(t2("TRANSPORTED_ENTITY", "THEME", True, cls="Blood"),),
        tests=T(["The heart pumped blood."], ["Blood circulated."], ["BLOOD_CIRCULATION of water"],
                [("The heart pumped blood.", "The pump moved water.")])),
    FrameDef(
        "FLUID_CIRCULATION_SYSTEM", 2, G, SK.SYSTEM,
        roles=(t2("DRIVER", "INSTRUMENT", True), t2("FLUID", "THEME", True, cls="Fluid"), t2("CONDUIT", "PATH")),
        final=(SP("DRIVES_FLOW_OF", ("DRIVER", "FLUID")), SP("FLOWS_THROUGH", ("FLUID", "CONDUIT"))), applies_when="ALWAYS",
        role_functions=(("DRIVER", "FN.DRIVE_FLUID_FLOW"), ("CONDUIT", "FN.CONDUCT_FLUID")),
        tests=T(["The heart, blood and vessels form a circulation system."], ["A pump drives water. (conduit unspecified)"],
                ["a fan driving air requires no conduit: CONDUIT must stay OPTIONAL"], [("The heart drives blood.", "The heart contains blood.")]),
        doc="structural frame: analogies align roles through FN functions, not through classes"),
)

SPEC_KERNEL_20 = (
    "STATE_CHANGE", "EXPERIENCE_STATE", "MOVE", "TRANSFER", "GIVE", "RETURN", "COMMERCIAL_TRANSACTION", "OWN", "WORK",
    "PERCEIVE", "COMMUNICATE", "BELIEVE", "KNOW", "WANT", "ATTEMPT", "OFFER", "CAUSATION", "EXAMINATION", "TREAT", "EAT",
)


# Completion of the Part 4 catalogue. These are representation schemas, not
# claims that every natural-language realization is implemented by the parser.
def _tests(name):
    return T([f"{name}: all required roles supplied"], [f"{name}: required roles explicitly unspecified"],
             [f"{name}: unknown role rejected"], [(f"{name} description", f"negated {name} description")])


_transform_roles = (t2("INPUT", "SOURCE", True), t2("PROCESS", "MANNER", kind=K.PROCESS), t2("OUTPUT", "GOAL", True))
FRAMES += (
    FrameDef("LEND", 1, G, parents=spec_of("GIVE"), tests=T(["John lent Mary a book."], ["John lent a book."],
             ["LEND with a bare concept filler"], [("John lent Mary a book.", "John gave Mary a book.")]),
             doc="Temporary possession transfer; ownership is not entailed."),
    FrameDef("HEAT", 1, G, parents=spec_of("STATE_CHANGE"), pins=(("DIMENSION", "Temperature"), ("DIRECTION", "INCREASE")),
             roles=(t1("UNDERGOER", True, cls="PhysicalEntity"),), tests=_tests("HEAT")),
    FrameDef("COOL", 1, G, parents=spec_of("STATE_CHANGE"), pins=(("DIMENSION", "Temperature"), ("DIRECTION", "DECREASE")),
             roles=(t1("UNDERGOER", True, cls="PhysicalEntity"),), tests=_tests("COOL")),
    FrameDef("TRANSFORMATION", 1, G, abstract=True, roles=_transform_roles, tests=_tests("TRANSFORMATION")),
    FrameDef("PHYSICAL_TRANSFORMATION", 1, G, parents=spec_of("TRANSFORMATION"),
             roles=(t2("INPUT", "SOURCE", True, cls="PhysicalEntity"), t2("OUTPUT", "GOAL", True, cls="PhysicalEntity")), tests=_tests("PHYSICAL_TRANSFORMATION")),
    FrameDef("INFORMATION_TRANSFORMATION", 1, G, parents=spec_of("TRANSFORMATION"),
             roles=(t2("INPUT", "SOURCE", True, cls="Information"), t2("OUTPUT", "GOAL", True, cls="Information")), tests=_tests("INFORMATION_TRANSFORMATION")),
    FrameDef("STATE_TRANSITION", 1, G, parents=spec_of("STATE_CHANGE"), tests=_tests("STATE_TRANSITION")),
    FrameDef("RELATIONAL_TRANSFORMATION", 1, G, parents=spec_of("TRANSFORMATION"), tests=_tests("RELATIONAL_TRANSFORMATION")),
    FrameDef("COMBINE", 1, G, abstract=True,
             roles=(RoleDecl("INPUTS", 2, "SOURCE", K.ENTITY, None, True, 64, 2), t2("RESULT", "GOAL", True)), tests=_tests("COMBINE")),
    FrameDef("SEPARATE", 1, G, abstract=True,
             roles=(t1("SOURCE", True), RoleDecl("OUTPUTS", 2, "GOAL", K.ENTITY, None, True, 64, 2)), tests=_tests("SEPARATE")),
    FrameDef("COMPARE", 1, G, roles=(t1("AGENT"), RoleDecl("ITEMS", 2, "THEME", K.ENTITY, None, True, 64, 2),
                                                    t2("CRITERION", "MANNER", kind=K.PROPERTY), t2("RESULT", "GOAL", kind=K.VALUE)), tests=_tests("COMPARE")),
    FrameDef("SELECT", 1, G, roles=(t1("AGENT"), t2("OPTIONS", "SOURCE", True, card=64), t2("SELECTED", "GOAL", True)), tests=_tests("SELECT")),
    FrameDef("CREATE", 1, G, roles=(t1("AGENT"), t2("CREATED_ENTITY", "GOAL", True)), tests=_tests("CREATE")),
    FrameDef("DESTROY", 1, G, roles=(t1("AGENT"), t1("UNDERGOER", True)), tests=_tests("DESTROY")),
    FrameDef("STORE", 1, G, roles=(t2("HOLDER", "LOCATION", True), t2("HELD", "THEME", True), t1("TIME", kind=K.TIME)), tests=_tests("STORE")),
    FrameDef("CONTAINMENT", 1, G, SK.STATE, roles=(t2("CONTAINER", "LOCATION", True), t1("CONTENT", True)), tests=_tests("CONTAINMENT")),
    FrameDef("INTERACTION", 1, G, roles=(RoleDecl("PARTICIPANTS", 2, "COMITATIVE", K.ENTITY, None, True, 64, 2),), tests=_tests("INTERACTION")),
    FrameDef("COMPOSITE_STRUCTURE", 1, G, SK.SYSTEM, roles=(t2("WHOLE", "THEME", True), t2("PART", "COMITATIVE", True, card=64)), tests=_tests("COMPOSITE_STRUCTURE")),
    FrameDef("ENERGY_STORAGE", 2, G, parents=spec_of("STORE"), role_functions=(("HOLDER", "FN.STORE_ENERGY"),), tests=_tests("ENERGY_STORAGE")),
    FrameDef("INFORMATION_PROCESSING", 2, G, parents=spec_of("INFORMATION_TRANSFORMATION"), tests=_tests("INFORMATION_PROCESSING")),
    FrameDef("MATERIAL_TRANSFORMATION", 2, G, parents=spec_of("PHYSICAL_TRANSFORMATION"), tests=_tests("MATERIAL_TRANSFORMATION")),
    FrameDef("ELECTRICAL_ENERGY_STORAGE", 3, D, parents=spec_of("ENERGY_STORAGE"), tests=_tests("ELECTRICAL_ENERGY_STORAGE"),
             doc="Electrical energy distinction requires a domain extension; no unstated constraints are inferred."),
    FrameDef("CHEMICAL_REACTION", 3, D, parents=spec_of("MATERIAL_TRANSFORMATION"), tests=_tests("CHEMICAL_REACTION")),
    FrameDef("FINANCIAL_TRANSACTION", 3, D, parents=spec_of("COMMERCIAL_TRANSACTION"), tests=_tests("FINANCIAL_TRANSACTION")),
)
