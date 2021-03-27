Vision and Guiding Priniciples
==============================

* Generating consistent and realistic test data should be **easy**. The more
  effort it is to produce releastic or consistent test data, the more likely
  developers take short cuts. This tends to couple tests to the implementation
  (e.g., because only the fields required for a specific implementation are set,
  or certain fields are inconsistent with the values of other fields). It also
  makes it harder to understand, based on the tests, what the expected
  production data will look like, or can be outright confusing.
* The code should be **declarative**. When creating test data one should not be
  concerned with *how* it is created, but with *what* the structure of that
  data.
* Try **minimize boilerplate** to reduce the effort of producing consistent and
  realistic test data (see above).
* To be able to easily create complex and varied test data, things should be
  **composable**.
* Test results should be **reproducible**. Thus, all test data will be generated
  based on a fixed (but changeable) seed. Plato even tries to keep produced
  values reproducible when fields are added or deleted from a class.
* One should have **flexibility** in how the generated data is used. Therefore,
  Plato produces dataclasses as output, that can be easily converted into
  dictionaries and other sorts of objects.
* **No collisions** of field names in the test data with Plato's API. This is
  achieved similar to dataclasses by not defining Plato's API as member methods
  on the formclasses, but as separate functions processing a formclass.